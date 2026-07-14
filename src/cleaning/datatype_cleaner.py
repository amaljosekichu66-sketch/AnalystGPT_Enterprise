from pandas import DataFrame


class DataTypeCleaner:
    """
    Converts DataFrame columns to the required data types.
    """

    def __init__(self, datatype_map=None):
        """
        datatype_map example:

        {
            "age": "int",
            "salary": "float",
            "joining_date": "datetime",
            "name": "string"
        }
        """

        self.datatype_map = datatype_map or {}

    def clean(self, dataframe: DataFrame) -> DataFrame:
        """
        Convert columns to the specified data types.
        """

        for column, datatype in self.datatype_map.items():

            if column not in dataframe.columns:
                continue

            try:

                if datatype == "datetime":
                    dataframe[column] = dataframe[column].astype("datetime64[ns]")

                else:
                    dataframe[column] = dataframe[column].astype(datatype)

            except Exception:

                print(f"Could not convert '{column}' to {datatype}")

        return dataframe