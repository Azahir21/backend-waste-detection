from fastapi import Depends, HTTPException

from src.repositories.repository_sampah import SampahRepository
from src.repositories.repository_user import UserRepository
from src.repositories.repository_statistic import StatisticRepository


class StatisticController:
    def __init__(
        self,
        statistic_repository: StatisticRepository = Depends(),
        user_repository: UserRepository = Depends(),
        sampah_repository: SampahRepository = Depends(),
    ):
        self.statistic_repository = statistic_repository
        self.user_repository = user_repository
        self.sampah_repository = sampah_repository

    async def get_total_statistic(self, token):
        try:
            return await self.statistic_repository.get_total_statistic(token)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_data_statistic(
        self,
        token,
        data_type: str,
        status: str,
        start_date,
        end_date,
        sort_by: str,
        sort_order: str,
        search: str,
        page: int,
        page_size: int,
    ):
        try:
            data, total_count = await self.statistic_repository.get_data_statistic(
                token,
                data_type,
                status,
                start_date,
                end_date,
                sort_by,
                sort_order,
                search,
                page,
                page_size,
            )
            total_pages = (total_count + page_size - 1) // page_size
            return {
                "data": data,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
