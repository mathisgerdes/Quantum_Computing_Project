import numpy as np

""" This module provides the State data structure. 

A State represents the full quantum mechanical state of a arbitrary but fix
number of qubits.

In analogy to a classical gate, this specifies the 'values' (0 or 1) of all
wires at a specific cross-section of a circuit. (Note here that quantum curcuits
are, as opposed to classical ones, linear. That means that along the circuit
the number of qubits doesn't change. This is equivalent to saying that along the
circuit no information is lost.) However, for a given number of (qu-)bits, the
quantum circuit can be in exponentially more states than a classical one.
This is because a state is generally a superposition of multiple 'classical',
un-entangled states. (A state can always be represented via a superposition of
basis states. The choice of basis states is arbitrary. In this implementation, 
we choose the 'intuitive' classical states as basis states. This choice of
basis is called 'computational basis'.) Therefore, a State object stores the
amplitudes of each basis state and provides methods to manipulate these.

A more technical and detailed explanation is provided in the State class.
"""

class State(object):
    """ Data structure representing the general state of a set of qubits.

    The state is represented via the amplitudes of each basis state.
    With basis states (here) always refer to the computational basis.

    The computational basis emerges from considering all individual settings
    of the qubits. Each qubit can individually be on or off (up or down),
    The total number of possible combinations is therefore 2 ^ qubit_count,
    where qubit_count is the number of qubits. This would classically also be
    the total number of possible configurations. Quantum mechanically, however,
    the system can be in an arbitrary superposition of these states.
    In the computational basis, we assign a number (label) to the
    configurations, as one does in classical computing.
    All states being down (off) corresponds to the value 0, the first bit up
    and the rest down is 1, the second bit up and the rest down is 2, etc.


    Example:
        A system with 3 qubits has 2 ^ 3 = 8 basis states.
        writing up as 1, down as 0 these states are
        |0>|0>|0>, |0>|0>|1>, |0>|1>|0>, |0>|1>|1>, ...
        (using order of computational basis)

        For convenience we write |c>|b>|a> = |cba> where a, b, c in {0, 1}.
        A basis state with label m in the computational basis is written |m>.
        The basis states for our 3 qubit system are therefore
        |000> = |0>, |001> = |1>, |010> = |2>
        |011> = |3>, |100> = |4>, |101> = |5>
        |110> = |6>, |111> = |7>.

        This is exactly how numbers are represented in classical,
        binary computers.

    Generally, a state |..., n_1, n_0> = | (sum n_k * 2 ^ k) >,
    where n_k in {0, 1} and k = 0, ..., qubit_count - 1.

    Note that in the states of the computational basis, the values of different
    qubits are not entangled. To represent a general state, including entangled
    qubits, we must allow superpositions of these basis states.

    Any state can be represented by specifying it's amplitudes regarding the
    computational basis (linear algebra).

    Example:
        In a 2 qubit system (omitting a factor 1/sqrt(2) for normalization):
        (|0> + |1>) |0> = |0> + |2>
        would represented as State([s2, 0, s2, 0]) where s2 = 1/sqrt(2)

        >>> s = State([1, 0, 1, 0])  # not normalized
        >>> print(s)
        1.000 |0> + 1.000 |2>
        >>> s.prob_of_bs(1)  # no chance of measuring system in state |1>
        0.0
        >>> s.prob_of_bs(0)  # method automatically considers norm
        0.5
        >>> s.prob_of_state(State.from_basis_state(2, 0))  # same as above
        0.5
        >>> s = s / s.norm() # normalize state
        >>> s.is_normalized()
        True
        >>> s.norm()
        0.99999999999999989

        In the last line, the limitation of this simulation become obvious:
        The square root of two cannot be accurately be represented using floats.
        This leads to a rounding error when calculating the norm.
        To test equality in these cases, use np.close.
    """
    def __init__(self, initial_state, dtype=np.complex128):
        """ Initialize state given a set of amplitudes.

        Example:
            >>> s = State([1, 0, 0, 0])
            >>> s
            array([ 1.+0.j,  0.+0.j,  0.+0.j,  0.+0.j])
            >>> print(s)
            1.000 |0>

        :param initial_state: Iterable, specifying amplitude for
            each basis state.
        :param dtype: Numeric type to be used for amplitudes.
        """
        self.dtype = dtype
        # The state is represented as amplitudes of constituent basis states.
        self.amplitudes = np.array(initial_state, dtype)
        self.basis_size = len(self.amplitudes)
        # For n qubits, there are 2**n basis states
        self.qubit_count = int(np.log2(self.basis_size))

        # assert initial_state has a power of two number of entries
        # note: 1 << n == 2 ** n
        assert 1 << self.qubit_count == self.basis_size

    def norm(self):
        """ Returns the sum of the squared amplitudes of the state.

        :return: float, norm of the state vector
        """
        # .real is necessary because norm should be a float.
        # (self * self).imag == 0, no information lost.
        return np.sqrt((self * self).real)

    def is_normalized(self, rtol=1e-5, atol=1e-8):
        """Checks if a State object is (close to being) normalized.

        It is normalized, if sum of squared amplitudes == 1.
        Uses the numpy function isclose.


        :param rtol: Relative tolarence, see np.isclose.
        :param atol: Absolute tolerance, see np.isclose.
        :return: Returns the Bool:
                    True if the object is close to being normalized
                    False if the object is not close to being normalized
        """
        return np.isclose(self.norm(), 1, rtol=rtol, atol=atol)

    def prob_of_bs(self, basis_state, normalize=True):
        """

        :param basis_state: The basis state of interest.
        :param normalize: Normalize state before calculating amplitudes.
        :return: The probability of the system being in the basis state
            of interest.
        """
        if normalize:
            return np.square(abs(self[basis_state])) / (self * self).real
        else:
            return np.square(abs(self[basis_state]))

    def prob_of_state(self, state, normalize=True):
        """The probability of a State being in particular State object.

        :param state: The state of interest (does NOT have to be a basis state,
            can be any State object)
        :param normalize: Normalize state before calculating amplitudes.
        :return: The probability of the system being in the state of interest
        """
        prob = np.square(abs(self * state))
        if normalize:
            # doing the calculation like this makes it more accurate
            norm = (self * self).real * (state * state).real
            return prob / norm
        else:
            return prob

    def random_measure_bs(self):
        """ Select a basis state with probabilities according to amplitudes.

        Make a random choice on the basis states each weighted with
        the probability of finding the system in that state
        (i.e. amplitude squared).

        To illustrate the implementation, consider the (2-qubit) state
        with amplitudes [0.25, 0.25, 0, 0.5] = 0.25|0> + 0.25|1> + 0.5|3>.
        The first step, conceptually, is to split the real numbers
        between 0 and 1 into chunks with sizes according to the probabilities
        of the basis states:
        0.0   0.25   0.5   0.75 1.0
        |     |      |     |    |
        00000|11111||33333 33333
        A random number (in [0, 1)) is generated and the basis state chosen
        is the one to which the block belongs, the random number is found in.
        By making blocks belonging to one basis state larger,
        it gets more probable this basis state will be measured.

        :return: The basis state which the state was measured to be in
        """
        sample = np.random.random_sample()  # random number in [0, 1)
        basis_state = 0  # start "checking" if it's in the 0th basis state
        acc = self.prob_of_bs(basis_state)
        # if we haven't measured that state, keep checking the next states
        while acc < sample:
            basis_state += 1
            acc += self.prob_of_bs(basis_state)
        return basis_state

    def random_measure_qubit(self, qubit):
        """ Randomly get state of one qubit according to state's probabilities.

        :type qubit: int
        :param qubit: Index of qubit to measure.
        :return: Either 0 or 1.
        """
        # sum of probabilities of basis states, for which qubit is set
        prob_set = sum(self.prob_of_bs(bs)
                       for bs in range(self.basis_size)
                       if (1 << qubit) & bs != 0)  # if (qu-)bit is set

        if np.random.random_sample() < prob_set:
            return 1
        else:
            return 0

    @classmethod
    def from_basis_state(cls, qubit_count, basis_state, dtype=np.complex128):
        """ Creates a State object that is a basis state, given its label.

        :param qubit_count: Number of qubits in the state
        :param basis_state: The basis state to create
        :param dtype: Numeric type to use for amplitudes in state.
        :return: State object in the basis state specified
        """
        state = np.zeros(1 << qubit_count, dtype)
        assert basis_state < 1 << qubit_count, 'Basis state is not valid.'
        state[basis_state] = 1.0
        return State(state, dtype=dtype)

    def __len__(self):
        """ Prevent the implementation of len.

        state must not implement len, otherwise multiplying a numpy data type
        and a state will result in __mul__ being (successfully) called on the
        numpy data type (which is possible because __getitem__ and __iter__ are
        implemented by State). This, however returns a new numpy array of the
        left hand data type, instead of a State (which is what we want).
        By raising an error here, this case results in __rmul__ being called
        on state, which is the correct behaviour.

        >>> s = np.complex128(42) * State.from_basis_state(4, 0)
        >>> type(s) == State # s must be a state, not (!) an ndarray
        True

        :return: Failure.
        """
        raise NotImplementedError()

    def __getitem__(self, item):
        """Return an amplitude of 1 basis state in the State object

        :param item: The basis state (int) to get the amplitude of
                    (equivalent to the index in the array of amplitudes)
        :return: The (complex) amplitude of the basis state
        """
        return self.amplitudes[item]

    def __setitem__(self, key, value):
        """Set an amplitude of 1 basis state in the State object

        :param key: The basis state (int) to set the amplitude of
                    (equivalent to the index in the array of amplitudes)
        :param value: The (complex) value to set the amplitude to
        :return: Nothing (modifies the State object being acted on)
        """
        self.amplitudes[key] = value

    def __eq__(self, state):
        # state can be any list of amplitudes, not necessarily of type State
        if isinstance(state, State) and self.qubit_count != state.qubit_count:
            return False

        for i, j in zip(self, state):
            if i != j:
                return False
        return True

    def __repr__(self):
        """The representation

        :return:
        """
        return "State with amplitudes " + self.amplitudes.__repr__()

    def __add__(self, state):
        """Add the amplitudes of two states

        :param state: the state object being added
        :return: State object resulting from the addition
        """
        return State(self.amplitudes + state.amplitudes)

    def __radd__(self, other):
        """ Support addition to zero (as neutral element).

        Do not explicitly call this.

        This method is needed to support the builtin sum method.
        Adding a state to 0 will yield the state:
        >>> s = State([0, 1])
        >>> (0 + s) == s
        True

        Executing 'state + state' will always lead to __add__ being called.
        Generally 'number + state' or 'state + number' is not supported,
        as the meaning of these statements is ambiguous.

        :param other: 0.
        :return: State(self).
        """
        if other == 0:
            return State(self.amplitudes)  # return a copy
        return self + other  # code execution should never come to this point

    def __sub__(self, state):
        """ Subtract amplitudes of one state by the amplitudes of another state

        :param state: the State object being subtracted by
        :return: State resulting from the subtraction
        """
        return State(self.amplitudes - state.amplitudes)

    def __neg__(self):
        """The additive inverse of a State object (in terms of its amplitudes)

        :return: State, with each amplitude element multiplied by -1
        """
        return State(-self.amplitudes)

    def __mul__(self, other):
        """ Multiply state and state or state and complex number

        :param other: State or complex number.
        :return: Depending on type of other:
            complex number -> state with amplitudes element wise multiplied
            state -> complex number <self|other>
        """
        if isinstance(other, State):
            return np.conj(self.amplitudes).dot(other.amplitudes)
        else:
            return State(other * self.amplitudes)

    def __rmul__(self, number):
        """Right multiplication of a state
        Only implemented for a state and a number

        :param number: Complex number being (right) multiplied by the state
        :return: State object with amplitudes multiplied element-wise
        """
        return self * number

    def __truediv__(self, number):
        """Divide a the amplitudes of a State object by a (complex) number, element-wise

        :param number: The (complex) number dividing the amplitudes
        :return: The State object, with it's amplitudes divided
        """
        return State(self.amplitudes / number)

    def __iter__(self):
        return self.amplitudes.__iter__()

    def __str__(self):
        parts = []

        if self.norm() == 0:
            return "0 |0>"

        def sign(num):
            """ Return sign of number as string. """
            return '+' if num > 0 else '-'

        for amp, label in zip(self, range(self.basis_size)):
            if amp == 0:
                continue

            imag, real = amp.imag, amp.real

            # separate each amplitude into
            # rep = [sign, number]
            # where *number* is a string representing a complex number.
            # List entries are later concatinated.

            if imag == 0:
                rep = [sign(real), '%.3f' % abs(real)]

            elif real == 0:
                rep = [sign(imag), '%.3fj' % abs(imag)]

            if imag < 0 and real < 0:
                rep = ['-', '%.3f %s j %.3f' % (-real, sign(-imag), -imag)]

            else:
                rep = ['+', '(%.3f + j %.3f)' % (real, imag)]

            rep.append('|' + str(label) + '>')

            if len(parts) == 0:     # if this is the first entry omit +
                if rep[0] == '-':
                    parts.append('-' + rep[1])
                    parts.append(rep[2])
                else:
                    parts.extend(rep[1:])
            else:
                parts.extend(rep)

        return " ".join(parts)
