from django.db.models import Q, Sum, Max, Prefetch, F

from rest_framework.views import APIView

from .serializers import LaunchpadLeaderBoardSerializer
from utils.response import CustomResponse
from utils.utils import CommonUtils
from db.user import User
from db.organization import UserOrganizationLink


class Leaderboard(APIView):
    def get(self, request):
        users = (
            User.objects.filter(
                karma_activity_log_user__task__event="launchpad",
                karma_activity_log_user__appraiser_approved=True,
                karma_activity_log_user__task__hashtag="#lp24-introduction",
            ).prefetch_related(
                Prefetch(
                    "user_organization_link_user",
                    queryset=UserOrganizationLink.objects.filter(
                        org__org_type__in=["College", "School", "Company", "Community"]
                    ),
                )
            )
            .annotate(
                karma=Sum(
                    "karma_activity_log_user__karma",
                    filter=Q(
                        karma_activity_log_user__task__event="launchpad",
                        karma_activity_log_user__appraiser_approved=True,
                    ),
                ),
                org=F("user_organization_link_user__org__title"),
                district_name=F("user_organization_link_user__org__district__name"),
                state=F("user_organization_link_user__org__district__zone__state__name"),
                time_=Max("karma_activity_log_user__created_at"),
            )
            .order_by("-karma", "time_")
        )

        paginated_queryset = CommonUtils.get_paginated_queryset(
            users,
            request,
            ["karma", "org", "district_name", "state", "time_"],
            sort_fields={
                "karma": "karma",
                "org": "org",
                "district_name": "district_name",
                "state": "state",
                "time_": "time_",
            },
        )

        serializer = LaunchpadLeaderBoardSerializer(
            paginated_queryset.get("queryset"), many=True
        )
        return CustomResponse().paginated_response(
            data=serializer.data, pagination=paginated_queryset.get("pagination")
        )
