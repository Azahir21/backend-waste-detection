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

    async def get_sampah_detail(self, token, sampah_id):
        data = await self.sampah_repository.get_sampah_detail(sampah_id)
        if data is None:
            raise HTTPException(status_code=404, detail="Sampah not found")
        data.image = f"https://jjmbm5rz-8000.asse.devtunnels.ms/garbage-image/{data.image.split('/')[-1]}"
        return data

    async def get_all_statistic(self, token):
        data = await self.statistic_repository.get_all_statistic(token)
        return data

    async def get_all_statistic_timeseries(self, token, start_date, end_date):
        return await self.statistic_repository.get_all_statistic_timeseries(
            token, start_date, end_date
        )

    async def get_garbage_pile_statistic(self, token):
        return await self.statistic_repository.get_garbage_pile_statistic(token)

    async def get_garbage_pile_statistic_timeseries(self, token, start_date, end_date):
        return await self.statistic_repository.get_garbage_pile_statistic_timeseries(
            token, start_date, end_date
        )

    async def get_garbage_pcs_statistic(self, token):
        return await self.statistic_repository.get_garbage_pcs_statistic(token)

    async def get_garbage_pcs_statistic_timeseries(self, token, start_date, end_date):
        return await self.statistic_repository.get_garbage_pcs_statistic_timeseries(
            token, start_date, end_date
        )
