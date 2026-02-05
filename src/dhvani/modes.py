class Modes:
    """To calculate acoustic mode frequencies within a open cavity flow
    """

    def __init__(self, u_inf, ref_len, mach_num):
        """

        :param u_inf: Free-stream velocity
        :param ref_len: reference length
        :param mach_num: Free-stream Mach number
        """

        self.u_inf = u_inf
        self.ref_len = ref_len
        self.Ma = mach_num

    def rossiter_modes(self, gamma=1.4, k=0.57, mode=1):
        """
        To acoustic mode frequencies within a low-speed open cavity flow using Rossiter's formula. For higher speeds,
         it is recommended to use Heller's formula

        :param gamma:  Ratio of specific heats
        :param k: k is a constant dependent on the cavity geometry and test
         conditions
        :param mode: mode of the frequency
        :return: frequency of mode m
        """

        u_by_l: float = self.u_inf / self.ref_len
        numerator = mode-gamma
        denominator = self.Ma + (1.0/k)

        f_m = u_by_l*(numerator/denominator)

        return f_m

    def heller_modes(self, gamma: float = 1.4, alpha: float = 0.25, k_nu: float = 0.57, mode: int = 1) -> float:
        """This is a modified Rossiter modes formula
        to compute PSD tones

        :param mode: mode of the frequency
        :param gamma: Ratio of specific heats
        :param alpha: represents phase shift
        :param k_nu: constant dependent on the cavity geometry and test conditions
        :return: frequency of mode m

        Notes
        -----
        Applicable to Mach number range 0.4 to 1.4

        Examples
        --------
        >>> modes = Modes(u_inf=289.4119498668744, ref_len=0.508, mach_num=0.85)
        >>> modes.heller_modes(mode=1)
        167.6325170837492
        """

        gamma_minus_1by2: float = (gamma - 1) * 0.5
        u_by_l: float = self.u_inf / self.ref_len
        num: float = mode - alpha
        den: float = self.Ma * (1 + gamma_minus_1by2 * self.Ma ** 2) ** (-0.5) + (1.0 / k_nu)
        f_m: float = u_by_l * num / den

        return f_m
