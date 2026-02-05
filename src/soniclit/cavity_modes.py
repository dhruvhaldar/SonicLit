class Modes:
    """To calculate acoustic mode frequencies within a open cavity flow
    """

    def __init__(self, freestream_velocity, reference_length, mach_number):
        """

        :param freestream_velocity: Free-stream velocity
        :param reference_length: reference length
        :param mach_number: Free-stream Mach number
        """

        self.freestream_velocity = freestream_velocity
        self.reference_length = reference_length
        self.mach_number = mach_number

    def rossiter_modes(self, gamma=1.4, empirical_constant_k=0.57, mode=1):
        """
        To acoustic mode frequencies within a low-speed open cavity flow using Rossiter's formula. For higher speeds,
         it is recommended to use Heller's formula

        :param gamma:  Ratio of specific heats
        :param empirical_constant_k: k is a constant dependent on the cavity geometry and test
         conditions
        :param mode: mode of the frequency
        :return: frequency of mode m
        """

        velocity_over_length: float = self.freestream_velocity / self.reference_length
        numerator = mode-gamma
        denominator = self.mach_number + (1.0/empirical_constant_k)

        mode_frequency = velocity_over_length*(numerator/denominator)

        return mode_frequency

    def heller_modes(self, gamma: float = 1.4, alpha: float = 0.25, empirical_constant_k_nu: float = 0.57, mode: int = 1) -> float:
        """This is a modified Rossiter modes formula
        to compute PSD tones

        :param mode: mode of the frequency
        :param gamma: Ratio of specific heats
        :param alpha: represents phase shift
        :param empirical_constant_k_nu: constant dependent on the cavity geometry and test conditions
        :return: frequency of mode m

        Notes
        -----
        Applicable to Mach number range 0.4 to 1.4

        Examples
        --------
        >>> modes = Modes(freestream_velocity=289.4119498668744, reference_length=0.508, mach_number=0.85)
        >>> modes.heller_modes(mode=1)
        167.6325170837492
        """

        gamma_minus_1by2: float = (gamma - 1) * 0.5
        velocity_over_length: float = self.freestream_velocity / self.reference_length
        num: float = mode - alpha
        den: float = self.mach_number * (1 + gamma_minus_1by2 * self.mach_number ** 2) ** (-0.5) + (1.0 / empirical_constant_k_nu)
        mode_frequency: float = velocity_over_length * num / den

        return mode_frequency
