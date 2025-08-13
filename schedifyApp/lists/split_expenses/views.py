import random
import string
from decimal import Decimal, ROUND_DOWN
from typing import Union

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from schedifyApp.CustomAuthentication import CustomAuthentication
from schedifyApp.lists.split_expenses.serializers import GroupSerializer, CollaboratorSerializer
from schedifyApp.login.models import EmailIdRegistration, AppUser
from .models import Group, Collaborator, Expense, ExpenseType
from .serializers import ExpenseSerializer
from ...communication.push_notification import sendSplitExpensePush
from ...communication.utils import ExpenseActionType, \
    CollaboratorActionType, _prepare_push_notify_title_msg, _prepare_push_notify_body_msg_for_collaborator, \
    _prepare_push_notify_body_msg_for_expense, _prepare_push_notify_body_msg_for_group, GroupActionType
from ...post_login.models import PostLoginUserDetail


def getFcmTokens(linked_user_id, actions: Union[GroupActionType, CollaboratorActionType, ExpenseActionType]) -> list:
    collaboratorsDetails = Collaborator.objects.filter(
        createdBy=linked_user_id,
        collabUserId__isnull=False
    ).select_related('collabUserId')

    # Extract all collaborator user IDs
    user_ids = [collab.collabUserId for collab in collaboratorsDetails]

    # Fetch all matching PostLoginUserDetail in one query
    fcm_tokens = list(
        PostLoginUserDetail.objects
        .filter(user_id__in=user_ids)
        .values_list("fcmToken", flat=True)
        .distinct()
    )

    print(f"Action : {actions.name} - fcm_tokens : {fcm_tokens}",)

    return fcm_tokens


class GroupAPIView(APIView):
    """
    Handles creation and retrieval of Groups for the authenticated user.
    """
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Fetches all groups where the user is a collaborator.
        Also resolves any pending invitations.
        """
        linked_user_id = request.app_user.id
        print("linked_user_id", linked_user_id)


        userEmailId = request.app_user.app_user_email

        print("userEmailId: ",userEmailId)

        # Resolve pending invitations
        pending_collaborators = Collaborator.objects.filter(
            collabEmailId=userEmailId
        )
        print("pending_collaborators", pending_collaborators)

        for pending in pending_collaborators:
            pending.collabUserId_id = linked_user_id
            pending.isActive = True
            pending.save()

        # Fetch groups associated with the user
        group_ids = Collaborator.objects.filter(
            collabUserId=linked_user_id
        ).values_list('groupId', flat=True)

        groups = Group.objects.filter(id__in=group_ids)
        serializer = GroupSerializer(groups, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Creates a new group and adds the current user as an active collaborator.
        """
        linked_user_id = request.app_user.id
        userEmailId = request.app_user.app_user_email
        data = request.data.copy()
        data['createdBy_id'] = linked_user_id

        serializer = GroupSerializer(data=data)
        if serializer.is_valid():
            group = serializer.save(createdBy_id=linked_user_id)
            collaborator_name = (userEmailId or "").split("@")[0] if userEmailId else "User@"+linked_user_id

            Collaborator.objects.create(
                groupId=group,
                collaboratorName = collaborator_name,
                createdBy_id=linked_user_id,
                collabUserId_id=linked_user_id,
                isActive=True
            )

            # Fetch groups associated with the user
            group_ids = Collaborator.objects.filter(
                collabUserId=linked_user_id
            ).values_list('groupId', flat=True)

            groups = Group.objects.filter(id__in=group_ids)
            serializer = GroupSerializer(groups, many=True)

            fcm_tokens = getFcmTokens(
                linked_user_id,
                actions=GroupActionType.GROUP_CREATION
            )

            sendSplitExpensePush(
                title=_prepare_push_notify_title_msg(GroupActionType.GROUP_CREATION),
                body=_prepare_push_notify_body_msg_for_group(
                    action=GroupActionType.GROUP_CREATION,
                    group=group,
                    groupAddedByEmailId=userEmailId
                ),
                tokens=fcm_tokens,
                pushNotificationType=GroupActionType.GROUP_CREATION
            )

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """
        Updates a group if the user is the creator.
        """
        group_id = request.query_params.get('group_id')

        if not group_id:
            return Response({"detail": "Group ID is required for patch."}, status=status.HTTP_400_BAD_REQUEST)

        linked_user_id = request.app_user.id
        userEmailId = request.app_user.app_user_email

        group = get_object_or_404(Group, id=group_id)
        groupOldName = group.name
        if group.createdBy_id != linked_user_id:
            return Response({"detail": "You do not have permission to update this group."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = GroupSerializer(group, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            fcm_tokens = getFcmTokens(
                linked_user_id,
                actions=GroupActionType.GROUP_UPDATION
            )

            sendSplitExpensePush(
                title=_prepare_push_notify_title_msg(GroupActionType.GROUP_UPDATION),
                body=_prepare_push_notify_body_msg_for_group(
                    action=GroupActionType.GROUP_UPDATION,
                    group=group,
                    groupOldName=groupOldName,
                    groupUpdatedByEmailId=userEmailId
                ),
                tokens=fcm_tokens,
                pushNotificationType=GroupActionType.GROUP_UPDATION
            )

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        Deletes a group if the user is the creator.
        """
        group_id = request.query_params.get('group_id')

        if not group_id:
            return Response({"detail": "Group ID is required for delete."}, status=status.HTTP_400_BAD_REQUEST)

        linked_user_id = request.app_user.id
        userEmailId = request.app_user.app_user_email

        group = get_object_or_404(Group, id=group_id)

        if group.createdBy_id != linked_user_id:
            return Response({"detail": "You do not have permission to delete this group."},
                            status=status.HTTP_403_FORBIDDEN)

        fcm_tokens = getFcmTokens(
            linked_user_id,
            actions=GroupActionType.GROUP_DELETION
        )

        group = get_object_or_404(Group, id=group_id)

        sendSplitExpensePush(
            title=_prepare_push_notify_title_msg(GroupActionType.GROUP_DELETION),
            body=_prepare_push_notify_body_msg_for_group(
                action=GroupActionType.GROUP_DELETION,
                group=group,
                groupDeletedByEmailId=userEmailId
            ),
            tokens=fcm_tokens,
            pushNotificationType=GroupActionType.GROUP_DELETION
        )

        group.delete()
        return Response({"detail": "Group deleted successfully."}, status=status.HTTP_200_OK)


class CollaboratorAPIView(APIView):
    """
    Handles collaborators - listing and adding them to groups.
    """
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Fetches collaborators for a given group, or all created by the user.
        """
        group_id = request.query_params.get('groupId')

        if group_id:
            collaborators = Collaborator.objects.filter(groupId_id=group_id)
        else:
            collaborators = Collaborator.objects.filter(createdBy=request.app_user)

        serializer = CollaboratorSerializer(collaborators, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Adds a collaborator to a group, with a pending invitation
        if the user is not registered.
        """
        data = request.data.copy()
        email = data.get('emailId')
        group_id = data.get('groupId')
        linked_user_id = request.app_user.id
        userEmailId = request.app_user.app_user_email

        if not email or not group_id:
            return Response(
                {"detail": "emailId and groupId are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data.update({
            'createdBy': linked_user_id,
            'collabEmailId': email,
            'isActive': False
        })

        try:
            user = AppUser.objects.get(app_user_email=email)
            data['collabUserId'] = user.id
        except EmailIdRegistration.DoesNotExist:
            data['collabUserId'] = None  # Will remain a pending invitation

        serializer = CollaboratorSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

            fcm_tokens = getFcmTokens(
                linked_user_id,
                actions=CollaboratorActionType.COLLABORATOR_CREATION
            )

            sendSplitExpensePush(
                title=_prepare_push_notify_title_msg(CollaboratorActionType.COLLABORATOR_CREATION),
                body= _prepare_push_notify_body_msg_for_collaborator(
                    action=CollaboratorActionType.COLLABORATOR_CREATION,
                    group= Group.objects.get(id=group_id),
                    collaboratorEmailId=email,
                    collaboratorAddedByEmailId=userEmailId
                ),
                tokens=fcm_tokens,
                pushNotificationType=CollaboratorActionType.COLLABORATOR_CREATION
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """
        Partially updates a collaborator by ID.
        """
        linked_user_id = request.app_user.id
        userEmailId = request.app_user.app_user_email

        collaborator_id = request.data.get('id')
        if not collaborator_id:
            return Response({"detail": "Collaborator ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        collaborator = get_object_or_404(Collaborator, id=collaborator_id)
        print(f"collaborator : {collaborator}")
        print(f"linked_user_id : {linked_user_id}")
        print(f"collaborator.createdBy : {collaborator.createdBy_id}")
        # Optional: Only allow patch if the requesting user is creator
        if collaborator.createdBy_id != linked_user_id:
            return Response({"detail": "You do not have permission to update this collaborator."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = CollaboratorSerializer(collaborator, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            data = request.data.copy()

            fcm_tokens = getFcmTokens(
                linked_user_id,
                actions=CollaboratorActionType.COLLABORATOR_UPDATION
            )

            sendSplitExpensePush(
                title= _prepare_push_notify_title_msg(CollaboratorActionType.COLLABORATOR_UPDATION),
                body= _prepare_push_notify_body_msg_for_collaborator(
                    action=CollaboratorActionType.COLLABORATOR_UPDATION,
                    group=Group.objects.get(id=collaborator.groupId_id),
                    collaboratorUpdatedByEmailId=userEmailId,
                    renamedClbName=data.get('collaboratorName')
                ),
                tokens=fcm_tokens,
                pushNotificationType=CollaboratorActionType.COLLABORATOR_UPDATION
            )

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        Deletes a collaborator by ID.
        """
        collaborator_id = request.query_params.get('id')
        linked_user_id = request.app_user.id
        userEmailId = request.app_user.app_user_email

        if not collaborator_id:
            return Response({"detail": "Collaborator ID is required in query params."},
                            status=status.HTTP_400_BAD_REQUEST)

        collaborator = get_object_or_404(Collaborator, id=collaborator_id)

        # Optional: Only allow to delete if the requesting user is creator
        if collaborator.createdBy_id != linked_user_id:
            return Response({"detail": "You do not have permission to delete this collaborator."},
                            status=status.HTTP_403_FORBIDDEN)

        # Get all expenses related to this collaborator (if any) and delete them
        expenses = Expense.objects.filter(expenseForCollaborator=collaborator_id)
        if expenses.exists():
            e_creation_id = expenses.first().eCreationId
            all_related_expenses = Expense.objects.filter(eCreationId=e_creation_id)
            print("expenses: ", all_related_expenses)
            all_related_expenses.delete()

        fcm_tokens = getFcmTokens(
            linked_user_id,
            actions=CollaboratorActionType.COLLABORATOR_DELETION
        )

        sendSplitExpensePush(
            title= _prepare_push_notify_title_msg(CollaboratorActionType.COLLABORATOR_DELETION),
            body=_prepare_push_notify_body_msg_for_collaborator(
                action=CollaboratorActionType.COLLABORATOR_DELETION,
                group=Group.objects.get(id=collaborator.groupId_id),
                collaboratorEmailId=collaborator.collabEmailId,
                deletedByEmailId=userEmailId
            ),
            tokens=fcm_tokens,
            pushNotificationType=CollaboratorActionType.COLLABORATOR_DELETION
        )
        collaborator.delete()
        return Response({"detail": "Collaborator deleted."}, status=status.HTTP_200_OK)


def _create_single_expense(data):
    data["eAmt"] = data.get("eRawAmt")
    serializer = ExpenseSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def _create_multiple_expenses(base_data, collaborators, added_by, group, linked_user_id):
    created_expenses = []
    total = collaborators.count()
    entry = base_data.copy()
    for collab in collaborators:

        entry["expenseForCollaborator"] = collab.id

        if base_data.get("eExpenseType") == "shared-equally":
            entry["eAmt"] = (Decimal(base_data["eRawAmt"]) / total).quantize(Decimal('.01'), rounding=ROUND_DOWN)

        serializer = ExpenseSerializer(data=entry)
        if serializer.is_valid():
            expense = serializer.save()
            created_expenses.append(ExpenseSerializer(expense).data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    fcm_tokens = getFcmTokens(
        linked_user_id,
        actions=ExpenseActionType.EXPENSE_CREATION
    )

    sendSplitExpensePush(
        title=f"{_prepare_push_notify_title_msg(ExpenseActionType.EXPENSE_CREATION)}",
        body=f"{_prepare_push_notify_body_msg_for_expense(
            action=ExpenseActionType.EXPENSE_CREATION,
            expenseDataRequestMap=entry,expenseAddedByEmailId=added_by, group=group)}",
        tokens=fcm_tokens,
        pushNotificationType=ExpenseActionType.EXPENSE_CREATION
    )

    return Response(created_expenses, status=status.HTTP_201_CREATED)


class ExpenseAPIView(APIView):

    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        group_id = request.query_params.get('groupId')
        collab_id = request.query_params.get('collaboratorId')

        if not group_id or not collab_id:
            return Response({'error': 'groupId and collaboratorId are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            group = Group.objects.get(id=group_id)
            caller_collaborator = Collaborator.objects.get(id=collab_id, groupId=group)
        except (Group.DoesNotExist, Collaborator.DoesNotExist):
            return Response({'error': 'Group or Collaborator not found'}, status=status.HTTP_404_NOT_FOUND)

        expenses = Expense.objects.filter(groupId=group).order_by('-created_on')

        self_list = []
        lend_list = []
        owe_list = []

        for expense in expenses:
            if expense.expenseForCollaborator is None:
                continue  # safety check

            # SELF
            if expense.addedByCollaboratorId.id == caller_collaborator.id and expense.expenseForCollaborator.id == caller_collaborator.id:
                self_list.append(ExpenseSerializer(expense).data)

            # LEND
            elif expense.addedByCollaboratorId.id == caller_collaborator.id and expense.expenseForCollaborator.id != caller_collaborator.id:
                lend_list.append(ExpenseSerializer(expense).data)

            # OWE
            elif expense.addedByCollaboratorId.id != caller_collaborator.id and expense.expenseForCollaborator.id == caller_collaborator.id:
                owe_list.append(ExpenseSerializer(expense).data)

        return Response({
            "self": self_list,
            "lend": lend_list,
            "owe": owe_list
        }, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data.copy()
        linked_user_id = request.app_user.id
        userEmailId = request.app_user.app_user_email

        try:
            group = Group.objects.get(id=data.get('groupId'))
            added_by = Collaborator.objects.get(id=data.get('addedByCollaboratorId'), groupId=group)
        except (Group.DoesNotExist, Collaborator.DoesNotExist):
            return Response({'error': 'Invalid group or collaborator'}, status=status.HTTP_400_BAD_REQUEST)

        expense_type = data.get('eExpenseType')
        e_raw_amt = data.get('eRawAmt')
        data["addedByCollaboratorId"] = added_by.id  # ensure consistency
        eCreationId = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        data["eCreationId"] = eCreationId
        data["eRawAmt"] = e_raw_amt

        if expense_type == "self":
            data["expenseForCollaborator"] = added_by.id
            return _create_single_expense(data)

        elif expense_type in ["shared-equally", "custom-split"]:
            collaborators = Collaborator.objects.filter(groupId=group)
            return _create_multiple_expenses(data, collaborators, userEmailId, group, linked_user_id)

        return Response({'error': 'Invalid expense type'}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        e_creation_id = request.query_params.get('eCreationId')
        data = request.data.copy()
        linked_user_id = request.app_user.id
        userEmailId = request.app_user.app_user_email
        updated_data = data.copy()

        try:
            group = Group.objects.get(id=data.get('groupId'))
            added_by = Collaborator.objects.get(id=data.get('addedByCollaboratorId'), groupId=group)
        except (Group.DoesNotExist, Collaborator.DoesNotExist):
            return Response({'error': 'Invalid group or collaborator'}, status=status.HTTP_400_BAD_REQUEST)

        expenses = Expense.objects.filter(eCreationId=e_creation_id)
        if not expenses.exists():
            return Response({'error': 'Expense not found'}, status=status.HTTP_404_NOT_FOUND)

        expense_type = data.get('eExpenseType')
        e_raw_amt = Decimal(data.get('eRawAmt'))
        data["eRawAmt"] = e_raw_amt

        if expense_type == "self":
            # Only one record should be updated
            expense = expenses.first()
            data["expenseForCollaborator"] = added_by.id
            serializer = ExpenseSerializer(expense, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif expense_type == "shared-equally":
            collaborators = Collaborator.objects.filter(groupId=group).order_by("id")
            expenses = expenses.order_by("expenseForCollaborator__id")

            if collaborators.count() != expenses.count():
                return Response(
                    {"error": "Collaborators and expenses count mismatch. Cannot perform update safely."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            total = collaborators.count()
            updated_expenses = []

            for collab, expense in zip(collaborators, expenses):
                updated_data["expenseForCollaborator"] = collab.id
                updated_data["eAmt"] = (e_raw_amt / total).quantize(Decimal('.01'), rounding=ROUND_DOWN)

                serializer = ExpenseSerializer(expense, data=updated_data, partial=True)
                if serializer.is_valid():
                    updated = serializer.save()
                    updated_expenses.append(ExpenseSerializer(updated).data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            fcm_tokens = getFcmTokens(
                linked_user_id,
                actions=ExpenseActionType.EXPENSE_UPDATION
            )

            sendSplitExpensePush(
                title=f"{_prepare_push_notify_title_msg(ExpenseActionType.EXPENSE_UPDATION)}",
                body=f"{_prepare_push_notify_body_msg_for_expense(
                    action=ExpenseActionType.EXPENSE_UPDATION,
                    expenseDataRequestMap=updated_data, expenseUpdatedByEmailId=added_by.collabUserId.emailId,
                    group=group)}",
                tokens=fcm_tokens,
                pushNotificationType=ExpenseActionType.EXPENSE_UPDATION
            )

            return Response(updated_expenses, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid expense type'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        eCreationId = request.query_params.get('eCreationId')
        linked_user_id = request.app_user.id
        userEmailId = request.app_user.app_user_email

        if not eCreationId:
            return Response({"error": "eCreationId is required."}, status=status.HTTP_400_BAD_REQUEST)

        expense = Expense.objects.filter(eCreationId=eCreationId).first()
        if not expense:
            return Response({"error": "Expense not found."}, status=status.HTTP_404_NOT_FOUND)

        expense_type = expense.eExpenseType

        if expense_type in [ExpenseType.SHARED_EQUALLY.value, ExpenseType.CUSTOM_SPLIT.value]:
            deleted_count, _ = Expense.objects.filter(eCreationId=eCreationId).delete()

            fcm_tokens = getFcmTokens(
                linked_user_id,
                actions=ExpenseActionType.EXPENSE_DELETION
            )

            group = Group.objects.get(id=expense.groupId_id)
            sendSplitExpensePush(
                title=f"{_prepare_push_notify_title_msg(ExpenseActionType.EXPENSE_DELETION)}",
                body=f"{_prepare_push_notify_body_msg_for_expense(
                    action=ExpenseActionType.EXPENSE_DELETION,
                    expenseDataObj=expense, expenseDeletedBy=userEmailId,
                    group=group)}",
                tokens=fcm_tokens,
                pushNotificationType=ExpenseActionType.EXPENSE_DELETION
            )

            return Response(
                {"detail": f"Expense deleted successfully ({deleted_count} items)."},
                status=status.HTTP_200_OK
            )
        else:
            # Delete only the single expense (SELF)
            expense.delete()
            return Response({"detail": "Expense deleted successfully."}, status=status.HTTP_200_OK)
