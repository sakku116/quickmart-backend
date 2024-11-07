
class CustomHttpException(Exception):
    """
    should be registered/added to fast api app to make this exception act like a HTTPException which is return json response.
    example:

    ```
    @app.exception_handler(MyHTTPException)
    async def my_http_exception_handler(request: Request, exc: MyHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=generic_resp.BaseResp(
                status="error",
                message=exc.message,
            ).dict(),
        )
    ```

    and when the exception is raised, it will return a json response. like:
    ```
    {
        "status": "error",
        "message": "internal server error"
    }
    ```
    and automatically change response.status_code to exc.status_code
    """
    def __init__(self, status_code=500, message="exception", data=None, detail="", context: dict = None):
        self.status_code = status_code
        self.message = message
        self.data = data
        self.detail = detail

        msg = f"{message}"
        if detail:
            msg = f"\nmsg: {message}\ndetail: {detail}"

        if context:
            if not detail:
                msg += f" | {context}"
            else:
                msg += f"\ncontext: {context}"

        super().__init__(msg)
