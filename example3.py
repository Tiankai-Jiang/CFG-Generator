def post(url, params=None, headers=None, retry=3, **kwargs):
    """
    :param url: 请求base url
    :param params: url params参数
    :param headers: http head头信息
    :param retry: 重试次数，默认retry=3
    :param kwargs: 透传给requests.get，可设置ua等，超时等参数
    """
    req_count = 0
    while req_count < retry:
        try:
            resp = requests.post(url=url, params=params, headers=headers, **kwargs)
            return resp
        except Exception as e:
            logging.exception(e)
            req_count += 1
            time.sleep(0.5)
            continue
    return None