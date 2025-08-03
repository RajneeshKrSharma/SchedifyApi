from enum import Enum

from enum import Enum
from typing import Union


class CollaboratorActionType(Enum):
    COLLABORATOR_CREATION = "COLLABORATOR_CREATION"
    COLLABORATOR_UPDATION = "COLLABORATOR_UPDATION"
    COLLABORATOR_DELETION = "COLLABORATOR_DELETION"

class ExpenseActionType(Enum):
    EXPENSE_CREATION = "EXPENSE_CREATION"
    EXPENSE_UPDATION = "EXPENSE_UPDATION"
    EXPENSE_DELETION = "EXPENSE_DELETION"

image_url_map = {
    CollaboratorActionType.COLLABORATOR_CREATION: "https://schedify.pythonanywhere.com/media/pictures/add_collaborator_image.png",
    CollaboratorActionType.COLLABORATOR_UPDATION: "https://schedify.pythonanywhere.com/media/pictures/update_collaborator_image.png",
    CollaboratorActionType.COLLABORATOR_DELETION: "https://schedify.pythonanywhere.com/media/pictures/delete_collaborator_image.png",
    ExpenseActionType.EXPENSE_CREATION: "https://schedify.pythonanywhere.com/media/pictures/add_expense_image.png",
    ExpenseActionType.EXPENSE_UPDATION: "https://schedify.pythonanywhere.com/media/pictures/update_expense_image.png",
    ExpenseActionType.EXPENSE_DELETION: "https://schedify.pythonanywhere.com/media/pictures/delete_expense_image.png",
}

def get_split_expense_image_url(
    pushNotificationType: Union[CollaboratorActionType, ExpenseActionType]
) -> str:
    return image_url_map.get(pushNotificationType, "")

from typing import Union

def _prepare_push_notify_title_msg(action: Union[ExpenseActionType, CollaboratorActionType]) -> str:
    title_map = {
        ExpenseActionType.EXPENSE_CREATION: "Expense Added !",
        ExpenseActionType.EXPENSE_UPDATION: "Expense Updated !",
        ExpenseActionType.EXPENSE_DELETION: "Expense Deleted !",
        CollaboratorActionType.COLLABORATOR_CREATION: "Collaborator Added !",
        CollaboratorActionType.COLLABORATOR_UPDATION: "Collaborator Updated !",
        CollaboratorActionType.COLLABORATOR_DELETION: "Collaborator Deleted !",
    }
    return title_map.get(action, "Notification")


def _prepare_push_notify_body_msg_for_expense(
        action: ExpenseActionType,
        group,
        expenseDataObj=None,
        expenseDataRequestMap=None,
        expenseAddedByEmailId="",
        expenseUpdatedByEmailId="",
        expenseDeletedBy=""
) -> str:
    print("action ->", action)

    if action == ExpenseActionType.EXPENSE_CREATION and expenseDataRequestMap:
        msg = (f"{expenseDataRequestMap['eName']} | {expenseDataRequestMap['eAmt']} , "
               f"by {expenseAddedByEmailId.split('@')[0]} in {group.name}")

    elif action == ExpenseActionType.EXPENSE_UPDATION and expenseDataRequestMap:
        msg = (f"{expenseDataRequestMap['eName']} | {expenseDataRequestMap['eAmt']} , "
               f"updated by {expenseUpdatedByEmailId.split('@')[0]} in {group.name}")

    elif action == ExpenseActionType.EXPENSE_DELETION and expenseDataObj:
        msg = (f"{expenseDataObj.eName} | {expenseDataObj.eAmt} , "
               f"deleted by {expenseDeletedBy.split('@')[0]} in {group.name}")

    else:
        msg = "Notification"

    print("msg ->", msg)
    return msg

def _prepare_push_notify_body_msg_for_collaborator(
        action: CollaboratorActionType,
        group,
        collaboratorEmailId="",
        collaboratorAddedByEmailId="",
        collaboratorUpdatedByEmailId="",
        renamedClbName="",
        deletedByEmailId="",

) -> str:
    try:
        if action == CollaboratorActionType.COLLABORATOR_CREATION:
            msg = (f"{collaboratorEmailId.split('@')[0]}, A new collaborator added by "
                   f"{collaboratorAddedByEmailId.split('@')[0]} in {group.name}")

        elif action == CollaboratorActionType.COLLABORATOR_UPDATION:
            msg = (f"Collaborator renamed to {renamedClbName} by "
                   f"{collaboratorUpdatedByEmailId.split('@')[0]} at {group.name}")

        elif action == CollaboratorActionType.COLLABORATOR_DELETION:
            msg = (f"{collaboratorEmailId.split('@')[0]} deleted by "
                   f"{deletedByEmailId.split('@')[0]} from {group.name}")
        else:
            msg = "Notification"
    except Exception as e:
        print(f"Error preparing collaborator notification: {e}")
        msg = "Notification"

    return msg

