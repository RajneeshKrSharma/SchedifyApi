from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from schedifyApp.post_login.models import HomeCarouselBanner, HomeCellAction, HomeCellDetails


class HomeBulkInsertAPIView(APIView):
    """
    POST API to insert banners & cells from one request.
    """

    def post(self, request):
        banners_data = request.data.get("home_carousel_banners", [])
        cells_data = request.data.get("home_cell_details", [])

        created_banners = []
        created_cells = []

        # Insert banners
        for banner in banners_data:
            obj = HomeCarouselBanner.objects.create(
                title=banner.get("title"),
                subtitle=banner.get("subtitle"),
                image_url=banner.get("image_url"),
                background_gradient_colors=banner.get("background_gradient_colors")
            )
            created_banners.append(obj.id)

        # Insert cells with related actions
        for cell in cells_data:
            action_instance = None
            action_data = cell.get("action")
            if action_data:
                action_instance = HomeCellAction.objects.create(
                    action_screen_name=action_data.get("action_screen_name", ""),
                    metadata=action_data.get("metadata", {})
                )

            obj = HomeCellDetails.objects.create(
                title=cell.get("title"),
                image_url=cell.get("image_url"),
                description=cell.get("description"),
                background_gradient_colors=cell.get("background_gradient_colors"),
                title_color=cell.get("title_color"),
                action=action_instance
            )
            created_cells.append(obj.id)

        return Response(
            {
                "message": "Data inserted successfully",
                "banners_created": created_banners,
                "cells_created": created_cells
            },
            status=status.HTTP_201_CREATED
        )
