
class SupportMixin(object):
    """混入类，声明数据源支持的市场，以及检测是否支持市场"""

    def _support_market(self):
        """声明数据源支持的市场，默认声明支持美股，港股，a股"""
        return [EMarketTargetType.E_MARKET_TARGET_US, EMarketTargetType.E_MARKET_TARGET_HK,
                EMarketTargetType.E_MARKET_TARGET_CN]

    def check_support(self, symbol=None, rs=True):
        """
        检测参数symbol对象或者内部self._symbol是否被数据源支持
        :param symbol: 外部可设置检测symbol对象，Symbol对象，EMarketTargetType对象或字符串对象
        :param rs: 如果数据源不支持，是否抛出异常，默认抛出
        :return: 返回是否支持 bool
        """
        if symbol is None:
            symbol = self._symbol

        if isinstance(symbol, six.string_types):
            # 如果是str，使用_support_market返回的value组成字符串数组，进行成员测试
            if symbol in [market.value for market in self._support_market()]:
                return True
        else:
            if isinstance(symbol, Symbol):
                # Symbol对象取market
                market = symbol.market
            elif isinstance(symbol, EMarketTargetType):
                market = symbol
            else:
                raise TypeError('symbol type is Symbol or str!!')
            # _support_market序列进行成员测试
            if market in self._support_market():
                return True

        if rs:
            #  根据rs设置，如果数据源不支持，抛出异常
            raise TypeError('{} don\'t support {}!'.format(self.__class__.__name__, symbol))
        return False
