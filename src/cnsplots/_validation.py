"""Validation utilities for cnsplots."""

from typing import Any, List, Optional, Union

import numpy as np
import pandas as pd

# ============================================================================
# Input Type Validation
# ============================================================================


def validate_dataframe(data: Any, param_name: str, function_name: str) -> None:
    """
    Validate that data is a pandas DataFrame.

    Parameters
    ----------
    data : Any
        The data to validate.
    param_name : str
        The name of the parameter being validated.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    TypeError
        If data is not a pandas DataFrame.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError(
            f"[{function_name}] Parameter '{param_name}' must be a pandas DataFrame, "
            f"got {type(data).__name__}"
        )


def validate_anndata(adata: Any, param_name: str, function_name: str) -> None:
    """
    Validate that adata is an AnnData object.

    Parameters
    ----------
    adata : Any
        The data to validate.
    param_name : str
        The name of the parameter being validated.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    TypeError
        If adata is not an AnnData object.
    """
    # Import here to avoid circular dependency
    try:
        from anndata import AnnData
    except ImportError:
        raise ImportError(
            f"[{function_name}] AnnData is required but not installed. "
            "Install with: pip install anndata"
        )

    if not isinstance(adata, AnnData):
        raise TypeError(
            f"[{function_name}] Parameter '{param_name}' must be an AnnData object, "
            f"got {type(adata).__name__}"
        )


# ============================================================================
# Column Validation
# ============================================================================


def validate_column_exists(
    data: pd.DataFrame, column: str, param_name: str, function_name: str
) -> None:
    """
    Validate that a column exists in a DataFrame.

    Parameters
    ----------
    data : pd.DataFrame
        The DataFrame to check.
    column : str
        The column name to validate.
    param_name : str
        The name of the parameter being validated.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If the column does not exist in the DataFrame.
    """
    if column not in data.columns:
        available = list(data.columns[:10])  # Show first 10 columns
        if len(data.columns) > 10:
            available_str = f"{available}... ({len(data.columns)} total columns)"
        else:
            available_str = str(available)

        raise ValueError(
            f"[{function_name}] Column '{column}' (specified in parameter '{param_name}') "
            f"not found in data. Available columns: {available_str}"
        )


def validate_columns_exist(
    data: pd.DataFrame, columns: List[str], function_name: str
) -> None:
    """
    Validate that multiple columns exist in a DataFrame.

    Parameters
    ----------
    data : pd.DataFrame
        The DataFrame to check.
    columns : List[str]
        The column names to validate.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If any column does not exist or a requested column name is duplicated in
        the DataFrame.
    """
    missing = [col for col in columns if col not in data.columns]
    if missing:
        available = list(data.columns[:10])
        if len(data.columns) > 10:
            available_str = f"{available}... ({len(data.columns)} total columns)"
        else:
            available_str = str(available)

        raise ValueError(
            f"[{function_name}] Column(s) {missing} not found in data. "
            f"Available columns: {available_str}"
        )

    duplicate_labels = data.columns[data.columns.duplicated(keep=False)]
    duplicates = [col for col in dict.fromkeys(columns) if col in duplicate_labels]
    if duplicates:
        raise ValueError(
            f"[{function_name}] Duplicate column name(s) {duplicates} found in data. "
            "Referenced columns must have unique names."
        )


# ============================================================================
# AnnData-Specific Validation
# ============================================================================


def validate_adata_layer(adata, layer: str, function_name: str) -> None:
    """
    Validate that a layer exists in an AnnData object.

    Parameters
    ----------
    adata : AnnData
        The AnnData object to check.
    layer : str
        The layer name to validate.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If the layer does not exist in adata.layers.
    """
    if layer not in adata.layers:
        available = list(adata.layers.keys())
        raise ValueError(
            f"[{function_name}] Layer '{layer}' not found in adata.layers. "
            f"Available layers: {available}"
        )


def validate_adata_obs_columns(
    adata, columns: Union[str, List[str]], function_name: str
) -> None:
    """
    Validate that columns exist in adata.obs.

    Parameters
    ----------
    adata : AnnData
        The AnnData object to check.
    columns : Union[str, List[str]]
        The column name(s) to validate.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If any column does not exist in adata.obs.
    """
    if isinstance(columns, str):
        columns = [columns]

    missing = [col for col in columns if col not in adata.obs.columns]
    if missing:
        available = list(adata.obs.columns[:10])
        if len(adata.obs.columns) > 10:
            available_str = f"{available}... ({len(adata.obs.columns)} total columns)"
        else:
            available_str = str(available)

        raise ValueError(
            f"[{function_name}] Column(s) {missing} not found in adata.obs. "
            f"Available columns: {available_str}"
        )


def validate_adata_var_columns(
    adata, columns: Union[str, List[str]], function_name: str
) -> None:
    """
    Validate that columns exist in adata.var.

    Parameters
    ----------
    adata : AnnData
        The AnnData object to check.
    columns : Union[str, List[str]]
        The column name(s) to validate.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If any column does not exist in adata.var.
    """
    if isinstance(columns, str):
        columns = [columns]

    missing = [col for col in columns if col not in adata.var.columns]
    if missing:
        available = list(adata.var.columns[:10])
        if len(adata.var.columns) > 10:
            available_str = f"{available}... ({len(adata.var.columns)} total columns)"
        else:
            available_str = str(available)

        raise ValueError(
            f"[{function_name}] Column(s) {missing} not found in adata.var. "
            f"Available columns: {available_str}"
        )


def validate_adata_uns_keys(
    adata, keys: Union[str, List[str]], function_name: str
) -> None:
    """Validate that keys exist in ``adata.uns``."""
    if isinstance(keys, str):
        keys = [keys]

    missing = [key for key in keys if key not in adata.uns]
    if missing:
        raise ValueError(
            f"[{function_name}] Key(s) {missing} not found in adata.uns. "
            f"Available keys: {list(adata.uns.keys())}"
        )


# ============================================================================
# Data Quality Validation
# ============================================================================


def validate_dataframe_not_empty(data: pd.DataFrame, function_name: str) -> None:
    """
    Validate that a DataFrame is not empty.

    Parameters
    ----------
    data : pd.DataFrame
        The DataFrame to check.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If the DataFrame is empty.
    """
    if data.empty:
        raise ValueError(
            f"[{function_name}] Data is empty. Cannot create plot with no data."
        )


def validate_no_nulls(
    data: pd.DataFrame,
    columns: Union[str, List[str]],
    function_name: str,
    allow_partial: bool = False,
) -> None:
    """
    Validate that columns have no null values.

    Parameters
    ----------
    data : pd.DataFrame
        The DataFrame to check.
    columns : Union[str, List[str]]
        The column name(s) to validate.
    function_name : str
        The name of the calling function for error messages.
    allow_partial : bool, default False
        If True, allow nulls when every column has valid values and at least one
        complete row remains. If False, raise an error if any null exists.

    Raises
    ------
    ValueError
        If columns contain null values (subject to allow_partial setting).
    """
    if isinstance(columns, str):
        columns = [columns]

    null_counts = {}
    for col in columns:
        null_count = data[col].isnull().sum()
        if null_count > 0:
            null_counts[col] = null_count

    if null_counts:
        if not allow_partial:
            details = ", ".join(
                [f"'{col}': {count}" for col, count in null_counts.items()]
            )
            raise ValueError(
                f"[{function_name}] Null values found in column(s) ({details}). "
                "Remove null values before plotting."
            )
        else:
            # Check if ALL values are null
            all_null_cols = [col for col in columns if data[col].isnull().all()]
            if all_null_cols:
                raise ValueError(
                    f"[{function_name}] Column(s) {all_null_cols} contain only null values. "
                    "At least some valid data is required."
                )
            if data[columns].dropna().empty:
                raise ValueError(
                    f"[{function_name}] Columns {columns} contain no complete rows. "
                    "At least one row without null values is required."
                )


def validate_column_type(
    data: pd.DataFrame, column: str, expected_types: List[str], function_name: str
) -> None:
    """
    Validate that a column has the expected data type.

    Parameters
    ----------
    data : pd.DataFrame
        The DataFrame to check.
    column : str
        The column name to validate.
    expected_types : List[str]
        List of acceptable type names (e.g., ['int', 'float', 'numeric']).
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If the column type is not in expected_types.
    """
    dtype = data[column].dtype

    # Map expected types to pandas dtypes
    numeric_types = ["int", "float", "number", "numeric"]

    if any(t in numeric_types for t in expected_types):
        if not pd.api.types.is_numeric_dtype(dtype):
            raise ValueError(
                f"[{function_name}] Column '{column}' must be numeric, got {dtype}"
            )
    elif (
        "object" in expected_types
        or "string" in expected_types
        or "categorical" in expected_types
    ):
        if (
            not pd.api.types.is_object_dtype(dtype)
            and not pd.api.types.is_string_dtype(dtype)
            and not isinstance(dtype, pd.CategoricalDtype)
        ):
            raise ValueError(
                f"[{function_name}] Column '{column}' must be categorical/string, "
                f"got {dtype}"
            )


def validate_sufficient_data(
    data: pd.DataFrame, column: str, min_count: int, function_name: str
) -> None:
    """
    Validate that a column has sufficient non-null values.

    Parameters
    ----------
    data : pd.DataFrame
        The DataFrame to check.
    column : str
        The column name to validate.
    min_count : int
        Minimum number of non-null values required.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If the column has fewer than min_count non-null values.
    """
    valid_count = data[column].notna().sum()
    if valid_count < min_count:
        raise ValueError(
            f"[{function_name}] Column '{column}' has only {valid_count} non-null values, "
            f"but at least {min_count} are required."
        )


def validate_binary_column(data: pd.DataFrame, column: str, function_name: str) -> None:
    """
    Validate that a column contains exactly the binary values 0 and 1.

    Parameters
    ----------
    data : pd.DataFrame
        The DataFrame to check.
    column : str
        The column name to validate.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If the column does not contain exactly 0 and 1.
    """
    unique_values = data[column].dropna().unique()
    if np.iscomplexobj(unique_values) or set(unique_values) != {0, 1}:
        raise ValueError(
            f"[{function_name}] Column '{column}' must have exactly 2 unique values, "
            f"specifically 0 and 1, found {list(unique_values)}"
        )


def validate_time_to_event_data(
    data: pd.DataFrame,
    duration: str,
    event: str,
    group: str,
    function_name: str,
    *,
    competing_risks: bool = False,
    min_groups: int = 1,
) -> None:
    """Validate durations, event codes, and per-group sample adequacy."""
    validate_column_type(data, duration, ["numeric"], function_name)
    validate_no_nulls(data, [duration, event, group], function_name)

    duration_values = data[duration].to_numpy()
    if np.iscomplexobj(duration_values) or pd.api.types.is_bool_dtype(
        data[duration].dtype
    ):
        raise ValueError(
            f"[{function_name}] Column '{duration}' must contain real-valued numeric "
            "durations."
        )
    durations = duration_values.astype(float)
    if not np.isfinite(durations).all():
        raise ValueError(
            f"[{function_name}] Column '{duration}' must contain only finite durations."
        )
    if (durations < 0).any():
        raise ValueError(
            f"[{function_name}] Column '{duration}' must contain only non-negative "
            "durations."
        )

    if competing_risks:
        validate_column_type(data, event, ["numeric"], function_name)
        raw_event_values = data[event].to_numpy()
        if np.iscomplexobj(raw_event_values):
            raise ValueError(
                f"[{function_name}] Column '{event}' must contain non-negative integer "
                "event codes (0 = censored, 1 = event of interest, 2+ = competing "
                "events)."
            )
        event_values = raw_event_values.astype(float)
        if (
            not np.isfinite(event_values).all()
            or (event_values < 0).any()
            or (event_values != np.floor(event_values)).any()
        ):
            raise ValueError(
                f"[{function_name}] Column '{event}' must contain non-negative integer "
                "event codes (0 = censored, 1 = event of interest, 2+ = competing "
                "events)."
            )
    else:
        validate_binary_column(data, event, function_name)

    group_sizes = data.groupby(group, observed=True).size()
    if len(group_sizes) < min_groups:
        raise ValueError(
            f"[{function_name}] Column '{group}' must contain at least {min_groups} "
            f"groups, found {len(group_sizes)}."
        )

    small_groups = group_sizes[group_sizes < 2]
    if not small_groups.empty:
        raise ValueError(
            f"[{function_name}] Each group in column '{group}' must contain at least 2 "
            f"observations; insufficient groups: {list(small_groups.index)}."
        )

    event_counts = (
        data.loc[data[event] == 1]
        .groupby(group, observed=True)
        .size()
        .reindex(group_sizes.index, fill_value=0)
    )
    groups_without_events = event_counts[event_counts < 1]
    if not groups_without_events.empty:
        raise ValueError(
            f"[{function_name}] Each group in column '{group}' must contain at least one "
            f"event of interest (event code 1); groups without events: "
            f"{list(groups_without_events.index)}."
        )


def validate_categorical_has_levels(
    data: pd.DataFrame,
    column: str,
    min_levels: Optional[int] = None,
    max_levels: Optional[int] = None,
    function_name: str = "",
) -> None:
    """
    Validate that a categorical column has an acceptable number of levels.

    Parameters
    ----------
    data : pd.DataFrame
        The DataFrame to check.
    column : str
        The column name to validate.
    min_levels : Optional[int]
        Minimum number of unique values required.
    max_levels : Optional[int]
        Maximum number of unique values allowed.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If the number of levels is outside the acceptable range.
    """
    n_levels = data[column].nunique()

    if min_levels is not None and n_levels < min_levels:
        raise ValueError(
            f"[{function_name}] Column '{column}' has {n_levels} unique values, "
            f"but at least {min_levels} are required."
        )

    if max_levels is not None and n_levels > max_levels:
        raise ValueError(
            f"[{function_name}] Column '{column}' has {n_levels} unique values, "
            f"but at most {max_levels} are allowed."
        )


def validate_numeric_range(
    data: pd.DataFrame,
    column: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    function_name: str = "",
) -> None:
    """
    Validate that numeric column values are within an acceptable range.

    Parameters
    ----------
    data : pd.DataFrame
        The DataFrame to check.
    column : str
        The column name to validate.
    min_val : Optional[float]
        Minimum acceptable value.
    max_val : Optional[float]
        Maximum acceptable value.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If any values are outside the acceptable range.
    """
    if min_val is not None:
        if (data[column] < min_val).any():
            raise ValueError(
                f"[{function_name}] Column '{column}' contains values less than {min_val}. "
                "All values must be within the acceptable range."
            )

    if max_val is not None:
        if (data[column] > max_val).any():
            raise ValueError(
                f"[{function_name}] Column '{column}' contains values greater than {max_val}. "
                "All values must be within the acceptable range."
            )


# ============================================================================
# Structure Validation
# ============================================================================


def validate_pairs_format(
    pairs: Any, data: pd.DataFrame, column: str, function_name: str
) -> None:
    """
    Validate that pairs parameter has correct format and values exist in column.

    Parameters
    ----------
    pairs : Any
        The pairs structure to validate (should be list of tuples or "all").
    data : pd.DataFrame
        The DataFrame containing the data.
    column : str
        The column name that pair values should reference.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If pairs format is invalid or references non-existent values.
    """
    # Allow special value "all"
    if isinstance(pairs, str) and pairs == "all":
        return

    if not isinstance(pairs, list):
        raise ValueError(
            f"[{function_name}] Parameter 'pairs' must be a list of tuples or 'all', "
            f"got {type(pairs).__name__}"
        )

    for i, pair in enumerate(pairs):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError(
                f"[{function_name}] Each pair must be a tuple/list of 2 elements, "
                f"but pair {i} is: {pair}"
            )

        # Check that values exist in the column
        available_values = data[column].unique()
        for val in pair:
            if val not in available_values:
                raise ValueError(
                    f"[{function_name}] Pair value '{val}' not found in column '{column}'. "
                    f"Available values: {list(available_values)}"
                )


def validate_length_match(
    list1: Any, list2: Any, name1: str, name2: str, function_name: str
) -> None:
    """
    Validate that two lists have matching lengths.

    Parameters
    ----------
    list1 : Any
        First list/array.
    list2 : Any
        Second list/array.
    name1 : str
        Name of first parameter.
    name2 : str
        Name of second parameter.
    function_name : str
        The name of the calling function for error messages.

    Raises
    ------
    ValueError
        If the lengths don't match.
    """
    len1 = len(list1) if hasattr(list1, "__len__") else 0
    len2 = len(list2) if hasattr(list2, "__len__") else 0

    if len1 != len2:
        raise ValueError(
            f"[{function_name}] Parameters '{name1}' and '{name2}' must have matching lengths, "
            f"got {len1} and {len2}"
        )


# ============================================================================
# Safe Operations
# ============================================================================


def safe_column_access(
    data: pd.DataFrame, column: str, function_name: str, default: Any = None
) -> Any:
    """
    Safely access a column with a default fallback.

    Parameters
    ----------
    data : pd.DataFrame
        The DataFrame to access.
    column : str
        The column name to access.
    function_name : str
        The name of the calling function for error messages.
    default : Any, default None
        Value to return if column doesn't exist.

    Returns
    -------
    Any
        The column data or default value.

    Raises
    ------
    ValueError
        If column doesn't exist and default is None.
    """
    if column not in data.columns:
        if default is None:
            raise ValueError(
                f"[{function_name}] Column '{column}' not found in data. "
                f"Available columns: {list(data.columns)}"
            )
        return default
    return data[column]


def safe_numeric_conversion(
    value: Any, function_name: str, context: str = ""
) -> Union[int, float]:
    """
    Safely convert a value to numeric, with helpful error on failure.

    Parameters
    ----------
    value : Any
        The value to convert.
    function_name : str
        The name of the calling function for error messages.
    context : str, default ""
        Additional context for the error message.

    Returns
    -------
    Union[int, float]
        The converted numeric value.

    Raises
    ------
    ValueError
        If conversion fails or value is NaN.
    """
    if pd.isna(value):
        context_str = f" ({context})" if context else ""
        raise ValueError(
            f"[{function_name}] Cannot convert NaN to numeric{context_str}. "
            "Ensure all required values are non-null."
        )

    try:
        return int(value) if isinstance(value, (int, np.integer)) else float(value)
    except (ValueError, TypeError) as e:
        context_str = f" ({context})" if context else ""
        raise ValueError(
            f"[{function_name}] Cannot convert value to numeric{context_str}: {value}"
        ) from e


def safe_division(
    numerator: float, denominator: float, default: float = np.nan
) -> float:
    """
    Safely perform division, returning default on division by zero.

    Parameters
    ----------
    numerator : float
        The numerator.
    denominator : float
        The denominator.
    default : float, default np.nan
        Value to return if denominator is zero.

    Returns
    -------
    float
        The result of division or default value.
    """
    if denominator == 0:
        return default
    return numerator / denominator
