from fastapi import Depends, HTTPException

from src.repositories.repository_sampah import SampahRepository
from src.repositories.repository_user import UserRepository
from src.repositories.repository_statistic import StatisticRepository
import pandas as pd
import io
from datetime import datetime
from fastapi.responses import StreamingResponse


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

    async def get_data_statistic_sheet(
        self,
        token,
        data_type: str,
        status: str,
        start_date,
        end_date,
        sort_by: str,
        sort_order: str,
        search: str,
        user: bool,
    ):
        try:
            result = await self.statistic_repository.get_data_statistic_sheet(
                token,
                data_type,
                status,
                start_date,
                end_date,
                sort_by,
                sort_order,
                search,
                user,
            )

            # Convert timezone-aware datetimes to naive datetimes
            for item in result:
                # Process each item in the result list
                for key, value in item.items():
                    # Check if the value is a datetime with timezone info
                    if (
                        isinstance(value, datetime)
                        and hasattr(value, "tzinfo")
                        and value.tzinfo
                    ):
                        # Convert to timezone naive by removing the timezone info
                        item[key] = value.replace(tzinfo=None)

            # Create DataFrame from the result
            df = pd.DataFrame(result)

            # Drop geom column as it contains complex objects that may cause Excel export issues
            if "geom" in df.columns:
                df = df.drop(columns=["geom"])

            # Additional safety: Convert any datetime columns to ensure they're timezone naive
            for col in df.select_dtypes(
                include=["datetime64[ns, UTC]", "datetimetz"]
            ).columns:
                df[col] = df[col].dt.tz_localize(None)

            # Create in-memory Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, sheet_name="Data", index=False)

                # Auto-adjust columns' width
                workbook = writer.book
                worksheet = writer.sheets["Data"]
                for i, col in enumerate(df.columns):
                    # Handle potential None values by converting to empty string
                    column_data = df[col].fillna("").astype(str)
                    column_width = max(column_data.map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, column_width)

            output.seek(0)

            # Generate filename with current date
            filename = f"statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            # Return the Excel file as a response
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except Exception as e:
            print(f"Error exporting to Excel: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
