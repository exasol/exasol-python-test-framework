"""Performance helpers."""
# pylint: disable=C0114,C0115,C0116,C0301,C0303,C0305,C0411,C0103,C0209,C0204,C0415,R1705,R1710,R1720,R1732,R0205,R0903,R0911,R0912,R0913,R0917,R1725,W0201,W0212,W0231,W0238,W0511,W0603,W0611,W0612,W0622,W0702,W0718,W0719,W1201,W1202,W1514,I1101

import time
from scipy import stats
import numpy as np

class MetricMeasurements:
    def __init__(self,metric_name, measurements):
        self._metric_name = metric_name
        self._measurements = measurements
        print("measurements:",self._measurements)
        array=np.array(self._measurements)
        self._stats = stats.describe(array)
        self._bayes_mvs = stats.bayes_mvs(array)

    @property
    def metric_name(self):
        return self._metric_name

    @property
    def mean(self):
        return self._stats.mean

    @property
    def maximum(self):
        return self._stats.minmax[1]
    
    @property
    def minimum(self):
        return self._stats.minmax[0]

    @property
    def variance(self):
        return self._stats.variance

    @property
    def skewness(self):
        return self._stats.skewness

    @property
    def kurtosis(self):
        return self._stats.kurtosis

    def __repr__(self):
        return \
            (
                'MetricMeasurements('
                'metric_name: {metric_name}\n'
                'mean: {mean}\n'
                'max: {maximum}\n'
                'min: {minimum}\n'
                'variance: {variance}\n'
                'skewness: {skewness}\n'
                'kurtosis: {kurtosis}\n'
                'bayes_mvs: {bayes_mvs}\n'
                ')'
            ).format(
                metric_name=self._metric_name,
                mean=self.mean,
                maximum=self.maximum,
                minimum=self.minimum,
                variance=self.variance,
                skewness=self.skewness,
                kurtosis=self.kurtosis,
                bayes_mvs=self._bayes_mvs
            )


class PerformanceMeasurementResults:
    def __init__(self, measurement_name, elapsed_times):
        self._measurement_name = measurement_name
        self._elapsed_time_measurements = MetricMeasurements("elapsed_time",elapsed_times)

    @property
    def measurement_name(self):
        return self._measurement_name

    def __repr__(self):
        elapsed_time_measurements=str(self._elapsed_time_measurements)
        return \
            (
                'MetricMeasurements('
                'measurement_name: {measurement_name}\n'
                'metrics: (\n'
                '{elapsed_time_measurements}\n'
                ')\n'
                ')'
            ).format(
                measurement_name=self._measurement_name,
                elapsed_time_measurements=elapsed_time_measurements
            )

def measure_query(conn, query):
    start = time.time()
    rows = conn.query(query)
    end = time.time()
    return end-start


def measure_query_repeated(connection, measurement_name, nb_of_runs, query):
    measurements = []
    for i in range(nb_of_runs):
        measurements.append(measure_query(connection, query))
    results = PerformanceMeasurementResults(measurement_name,measurements)
    return results


def run_performance_measurements(connection, test_name, runs, warmup, query):
    connection.query("alter session set query_cache='off'")
    warmup_results=measure_query_repeated(connection,test_name+"_WARMUP", warmup, query)
    measurement_results=measure_query_repeated(connection,test_name+"_MEASUREMENT", runs, query)
    return warmup_results, measurement_results
