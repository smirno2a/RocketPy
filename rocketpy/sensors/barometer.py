import numpy as np

from rocketpy.tools import export_sensors_measured_data

from ..mathutils.vector_matrix import Matrix
from ..prints.sensors_prints import _SensorPrints
from ..sensors.sensors import ScalarSensor


class Barometer(ScalarSensor):
    """Class for the barometer sensor

    Attributes
    ----------
    type : str
        Type of the sensor, in this case "Barometer".
    prints : _SensorPrints
        Object that contains the print functions for the sensor.
    sampling_rate : float
        Sample rate of the sensor in Hz.
    orientation : tuple, list
        Orientation of the sensor in the rocket.
    measurement_range : float, tuple
        The measurement range of the sensor in Pa.
    resolution : float
        The resolution of the sensor in Pa/LSB.
    noise_density : float
        The noise density of the sensor in Pa/√Hz.
    noise_variance : float
        The variance of the noise of the sensor in Pa^2.
    random_walk_density : float
        The random walk density of the sensor in Pa/√Hz.
    random_walk_variance : float
        The variance of the random walk of the sensor in Pa^2.
    constant_bias : float
        The constant bias of the sensor in Pa.
    operating_temperature : float
        The operating temperature of the sensor in degrees Celsius.
    temperature_bias : float
        The temperature bias of the sensor in Pa/°C.
    temperature_scale_factor : float
        The temperature scale factor of the sensor in %/°C.
    name : str
        The name of the sensor.
    measurement : float
        The measurement of the sensor after quantization, noise and temperature
        drift.
    measured_data : list
        The stored measured data of the sensor after quantization, noise and
        temperature drift.
    """

    units = "Pa"

    def __init__(
        self,
        sampling_rate,
        measurement_range=np.inf,
        resolution=0,
        noise_density=0,
        noise_variance=1,
        random_walk_density=0,
        random_walk_variance=1,
        constant_bias=0,
        operating_temperature=25,
        temperature_bias=0,
        temperature_scale_factor=0,
        name="Barometer",
    ):
        """
        Initialize the barometer sensor

        Parameters
        ----------
        sampling_rate : float
            Sample rate of the sensor in Hz.
        measurement_range : float, tuple, optional
            The measurement range of the sensor in the Pa. If a float, the same
            range is applied both for positive and negative values. If a tuple,
            the first value is the positive range and the second value is the
            negative range. Default is np.inf.
        resolution : float, optional
            The resolution of the sensor in Pa/LSB. Default is 0, meaning no
            quantization is applied.
        noise_density : float, optional
            The noise density of the sensor for a Gaussian white noise in Pa/√Hz.
            Sometimes called "white noise drift", "angular random walk" for
            gyroscopes, "velocity random walk" for accelerometers or
            "(rate) noise density". Default is 0, meaning no noise is applied.
        noise_variance : float, optional
            The noise variance of the sensor for a Gaussian white noise in Pa^2.
            Default is 1, meaning the noise is normally distributed with a
            standard deviation of 1 Pa.
        random_walk_density : float, optional
            The random walk of the sensor for a Gaussian random walk in Pa/√Hz.
            Sometimes called "bias (in)stability" or "bias drift"". Default is 0,
            meaning no random walk is applied.
        random_walk_variance : float, optional
            The random walk variance of the sensor for a Gaussian random walk in
            Pa^2. Default is 1, meaning the noise is normally distributed with a
            standard deviation of 1 Pa.
        constant_bias : float, optional
            The constant bias of the sensor in Pa. Default is 0, meaning no
            constant bias is applied.
        operating_temperature : float, optional
            The operating temperature of the sensor in degrees Celsius. At 25°C,
            the temperature bias and scale factor are 0. Default is 25.
        temperature_bias : float, optional
            The temperature bias of the sensor in Pa/°C. Default is 0, meaning no
            temperature bias is applied.
        temperature_scale_factor : float, optional
            The temperature scale factor of the sensor in %/°C. Default is 0,
            meaning no temperature scale factor is applied.
        name : str, optional
            The name of the sensor. Default is "Barometer".

        Returns
        -------
        None

        See Also
        --------
        TODO link to documentation on noise model
        """
        super().__init__(
            sampling_rate=sampling_rate,
            measurement_range=measurement_range,
            resolution=resolution,
            noise_density=noise_density,
            noise_variance=noise_variance,
            random_walk_density=random_walk_density,
            random_walk_variance=random_walk_variance,
            constant_bias=constant_bias,
            operating_temperature=operating_temperature,
            temperature_bias=temperature_bias,
            temperature_scale_factor=temperature_scale_factor,
            name=name,
        )
        self.type = "Barometer"
        self.prints = _SensorPrints(self)

    def measure(self, time, **kwargs):
        """Measures the pressure at barometer location

        Parameters
        ----------
        time : float
            Current time in seconds.
        kwargs : dict
            Keyword arguments dictionary containing the following keys:
            - u : np.array
                State vector of the rocket.
            - u_dot : np.array
                Derivative of the state vector of the rocket.
            - relative_position : np.array
                Position of the sensor relative to the rocket center of mass.
            - gravity : float
                Gravitational acceleration in m/s^2.
            - pressure : Function
                Atmospheric pressure profile as a function of altitude in Pa.
            - elevation : float
                Elevation of the launch site in meters.
        """
        u = kwargs["u"]
        relative_position = kwargs["relative_position"]
        pressure = kwargs["pressure"]

        # Calculate the altitude of the sensor
        relative_altitude = (Matrix.transformation(u[6:10]) @ relative_position).z

        # Calculate the pressure at the sensor location and add noise
        P = pressure(relative_altitude + u[2])
        P = self.apply_noise(P)
        P = self.apply_temperature_drift(P)
        P = self.quantize(P)

        self.measurement = P
        self._save_data((time, P))

    def export_measured_data(self, filename, file_format="csv"):
        """Export the measured values to a file

        Parameters
        ----------
        filename : str
            Name of the file to export the values to
        file_format : str
            file_format of the file to export the values to. Options are "csv" and
            "json". Default is "csv".

        Returns
        -------
        None
        """
        export_sensors_measured_data(
            sensor=self,
            filename=filename,
            file_format=file_format,
            data_labels=("t", "pressure"),
        )