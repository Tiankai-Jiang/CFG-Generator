class AbuBenchmark(PickleStateMixin):
    """基准类，混入PickleStateMixin，因为在abu.store_abu_result_tuple会进行对象本地序列化"""

    def __init__(self, benchmark=None, start=None, end=None, n_folds=2, rs=True, benchmark_kl_pd=None):
        if benchmark_kl_pd is not None and hasattr(benchmark_kl_pd, 'name'):
            """从金融时间序列直接构建"""
            self.benchmark = benchmark_kl_pd.name
            self.start = benchmark_kl_pd.iloc[0].date
            self.end = benchmark_kl_pd.iloc[-1].date
            self.n_folds = n_folds
            self.kl_pd = benchmark_kl_pd
            return

        if benchmark is None:
            if ABuEnv.g_market_target == EMarketTargetType.E_MARKET_TARGET_US:
                # 美股
                benchmark = IndexSymbol.IXIC
            elif ABuEnv.g_market_target == EMarketTargetType.E_MARKET_TARGET_HK:
                # 港股
                benchmark = IndexSymbol.HSI
            else:
                raise TypeError('benchmark is None AND g_market_target ERROR!')

        self.benchmark = benchmark
        self.start = start
        self.end = end
        self.n_folds = n_folds
        # 基准获取数据使用data_mode=EMarketDataSplitMode.E_DATA_SPLIT_SE，即不需要对齐其它，只需要按照时间切割
        self.kl_pd = ABuSymbolPd.make_kl_df(benchmark, data_mode=EMarketDataSplitMode.E_DATA_SPLIT_SE,
                                            n_folds=n_folds,
                                            start=start, end=end)

        if rs and self.kl_pd is None:
            # 如果基准时间序列都是none，就不要再向下运行了
            raise ValueError('CapitalClass init benchmark kl_pd is None')

    def unpick_extend_work(self, state):
        """完成 PickleStateMixin中__setstate__结束之前的工作，为kl_pd.name赋予准确的benchmark"""
        if isinstance(self.benchmark, Symbol):
            self.kl_pd.name = self.benchmark.value
        elif isinstance(self.benchmark, six.string_types):
            self.kl_pd.name = self.benchmark

    def __str__(self):
        """打印对象显示：benchmark n_folds"""
        return 'benchmark is {}, n_folds = {}'.format(self.kl_pd.name, self.n_folds)

    __repr__ = __str__
