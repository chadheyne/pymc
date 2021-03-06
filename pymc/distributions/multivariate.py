from .dist_math import *

__all__ = ['MvNormal', 'Dirichlet', 'Multinomial', 'Wishart']

from theano.sandbox.linalg import det, solve, trace
from theano.tensor import dot


@tensordist(continuous)
def MvNormal(mu, tau):
    """
    Multivariate normal

    :Parameters:
        mu : vector of means
        tau : precision matrix

    .. math::
        f(x \mid \pi, T) = \frac{|T|^{1/2}}{(2\pi)^{1/2}} \exp\left\{ -\frac{1}{2} (x-\mu)^{\prime}T(x-\mu) \right\}

    :Support:
        2 array of floats
    """

    def logp(value):
        delta = value - mu
        k = tau.shape[0]

        return 1/2. * (-k * log(2*pi) + log(det(tau)) - dot(delta.T, dot(tau, delta)))

    mean = median = mode = mu

    return locals()


@tensordist(continuous)
def Dirichlet(k, a):
    """
    Dirichlet

    This is a multivariate continuous distribution.

    .. math::
        f(\mathbf{x}) = \frac{\Gamma(\sum_{i=1}^k \theta_i)}{\prod \Gamma(\theta_i)}\prod_{i=1}^{k-1} x_i^{\theta_i - 1}
        \cdot\left(1-\sum_{i=1}^{k-1}x_i\right)^\theta_k

    :Parameters:
        k : scalar int
            k > 1
        a : float tensor
            a > 0
            concentration parameters
            last index is the k index

    :Support:
        x : vector
            sum(x) == 1 and x > 0

    .. note::
        Only the first `k-1` elements of `x` are expected. Can be used
        as a parent of Multinomial and Categorical nevertheless.
    """

    a = ones([k]) * a

    def logp(value):

        # only defined for sum(value) == 1
        return bound(
            sum(logpow(
                value, a - 1) - gammaln(a), axis=0) + gammaln(sum(a)),

            k > 1,
            a > 0)

    mean = a / sum(a)

    mode = switch(all(a > 1),
                 (a - 1) / sum(a - 1),
                  nan)

    return locals()


@tensordist(discrete)
def Multinomial(n, p):
    """
    Generalization of the binomial
    distribution, but instead of each trial resulting in "success" or
    "failure", each one results in exactly one of some fixed finite number k
    of possible outcomes over n independent trials. 'x[i]' indicates the number
    of times outcome number i was observed over the n trials.

    .. math::
        f(x \mid n, p) = \frac{n!}{\prod_{i=1}^k x_i!} \prod_{i=1}^k p_i^{x_i}

    :Parameters:
        n : int
            Number of trials.
        p : (k,)
            Probability of each one of the different outcomes.
            :math:`\sum_{i=1}^k p_i = 1)`, :math:`p_i \ge 0`.

    :Support:
        x : (ns, k) int
            Random variable indicating the number of time outcome i is
            observed. :math:`\sum_{i=1}^k x_i=n`, :math:`x_i \ge 0`.

    .. note::
        - :math:`E(X_i)=n p_i`
        - :math:`Var(X_i)=n p_i(1-p_i)`
        - :math:`Cov(X_i,X_j) = -n p_i p_j`
    """

    def logp(x):
        # only defined for sum(p) == 1
        return bound(
            factln(n) + sum(x * log(p) - factln(x)),
            n > 0,
            0 <= x, x <= n)

    mean = n * p

    return locals()


@tensordist(continuous)
def Wishart(n, p, V):
    """
    The Wishart distribution is the probability
    distribution of the maximum-likelihood estimator (MLE) of the precision
    matrix of a multivariate normal distribution. If tau=1, the distribution
    is identical to the chi-square distribution with n degrees of freedom.

    For an alternative parameterization based on :math:`C=T{-1}` (Not yet implemented)

    .. math::
        f(X \mid n, T) = \frac{{\mid T \mid}^{n/2}{\mid X \mid}^{(n-k-1)/2}}{2^{nk/2}
        \Gamma_p(n/2)} \exp\left\{ -\frac{1}{2} Tr(TX) \right\}

    where :math:`k` is the rank of X.

    :Parameters:
      n : int
        Degrees of freedom, > 0.
      tau : matrix
        Symmetric and positive definite

    :Support:
      X : matrix
        Symmetric, positive definite.
    """

    def logp(X):
        IVI = det(V)
        return bound(
            ((n - p - 1) * log(IVI) - trace(solve(V, X)) -
             n * p * log(
             2) - n * log(IVI) - 2 * multigammaln(p, n / 2)) / 2,

            n > p - 1)

    mean = n * V
    mode = switch(1*(n >= p + 1),
                 (n - p - 1) * V,
                  nan)

    return locals()
