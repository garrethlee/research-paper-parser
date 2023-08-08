from loguru import logger
import traceback


def log_traceback(func):
    """
    Decorator function that logs any exceptions raised by the wrapped function.

    Args:
        func (callable): The function to be wrapped.

    Returns:
        callable: The wrapped function that logs exceptions.

    Raises:
        Exception: If an exception is raised by the wrapped function.
    """

    def error_logged_func(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except:
            logger.error(
                f"Error occurred in '{func.__name__}': {traceback.format_exc()}"
            )
            raise Exception(
                f"Error occurred in '{func.__name__}': {traceback.format_exc()}"
            )

    return error_logged_func
