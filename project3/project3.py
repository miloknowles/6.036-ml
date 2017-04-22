import random
import time

import numpy as np


def k_means(data, k, eps=1e-4, mu=None):
    """ Run the k-means algorithm
    data - an NxD pandas DataFrame
    k - number of clusters to fit
    eps - stopping criterion tolerance
    mu - an optional KxD ndarray containing initial centroids

    returns: a tuple containing
        mu - a KxD ndarray containing the learned means
        cluster_assignments - an N-vector of each point's cluster index
    """
    if type(data) != type(np.array(0)): # if data is not a numpy array
        data = np.array(data) # convert it to one

    n, d = data.shape
    if mu is None:
        # randomly choose k points as initial centroids
        mu = data[random.sample(range(data.shape[0]), k)]

    # stores cluster index assigned to each of n points
    assignments = np.zeros(n)
    cluster_sizes = np.zeros(k)
    cluster_sums = np.zeros((k,d))

    # store the previous mu to detect when to stop
    prev_mu = np.zeros((k,d))

    converged = False
    iters = 0
    while (not converged):
        iters += 1
        print("Iter:", iters)

        # assign each point to the euclidean closest cluster
        for pt in range(n):
            cluster_id = 0
            best_euc_dist = float('inf')

            for u in range(k):
                resid = data[pt]-mu[u]
                euc_dist = np.linalg.norm(resid, ord=2)

                if euc_dist < best_euc_dist:
                    cluster_id = u
                    best_euc_dist = euc_dist

            assignments[pt] = cluster_id
            cluster_sizes[cluster_id] += 1
            cluster_sums[cluster_id] += data[pt]

        # recompute means: divide each cluster sum by the num pts. in that cluster
        for i in range(k):
            mu[i] = cluster_sums[i] / cluster_sizes[i]

        # check if converged
        for i in range(k):
            if np.linalg.norm((mu[i] - prev_mu[i]), ord=2) > eps: # if a mean has changed by more than epsilon
                converged = False
            else:
                converged = True

        # make sure this is here!
        prev_mu = mu
        
    return (mu, assignments)





class MixtureModel(object):
    def __init__(self, k):
        self.k = k
        self.params = {
            'pi': np.random.dirichlet([1]*k),
        }

    def __getattr__(self, attr):
        if attr not in self.params:
            raise AttributeError()
        return self.params[attr]

    def __setstate__(self, state):
        for k, v in state.items():
            setattr(self, k, v)

    def e_step(self, data):
        """ Performs the E-step of the EM algorithm
        data - an NxD pandas DataFrame

        returns a tuple containing
            (float) the expected log-likelihood
            (NxK ndarray) the posterior probability of the latent variables
        """
        raise NotImplementedError()

    def m_step(self, data, p_z):
        """ Performs the M-step of the EM algorithm
        data - an NxD pandas DataFrame
        p_z - an NxK numpy ndarray containing posterior probabilities

        returns a dictionary containing the new parameter values
        """
        raise NotImplementedError()

    @property
    def bic(self):
        """
        Computes the Bayesian Information Criterion for the trained model.
        Note: `n_train` and `max_ll` set during @see{fit} may be useful
        """
        raise NotImplementedError()

    def fit(self, data, eps=1e-4, verbose=True, max_iters=100):
        """ Fits the model to data
        data - an NxD pandas DataFrame
        eps - the tolerance for the stopping criterion
        verbose - whether to print ll every iter
        max_iters - maximum number of iterations before giving up

        returns a boolean indicating whether fitting succeeded

        if fit was successful, sets the following properties on the Model object:
          n_train - the number of data points provided
          max_ll - the maximized log-likelihood
        """
        last_ll = np.finfo(float).min
        start_t = last_t = time.time()
        i = 0
        while True:
            i += 1
            if i > max_iters:
                return False
            ll, p_z = self.e_step(data)
            new_params = self.m_step(data, p_z)
            self.params.update(new_params)
            if verbose:
                dt = time.time() - last_t
                last_t += dt
                print('iter %s: ll = %.5f  (%.2f s)' % (i, ll, dt))
                last_ts = time.time()
            if abs((ll - last_ll) / ll) < eps:
                break
            last_ll = ll

        setattr(self, 'n_train', len(data))
        setattr(self, 'max_ll', ll)
        self.params.update({'p_z': p_z})

        print('max ll = %.5f  (%.2f min, %d iters)' %
              (ll, (time.time() - start_t) / 60, i))

        return True


class GMM(MixtureModel):
    def __init__(self, k, d):
        super(GMM, self).__init__(k)
        self.params['mu'] = np.random.randn(k, d)

    def e_step(self, data):
        raise NotImplementedError()

    def m_step(self, data, pz_x):
        raise NotImplementedError()

        return {
            'pi': new_pi,
            'mu': new_mu,
            'sigsq': new_sigsq,
        }

    def fit(self, data, *args, **kwargs):
        self.params['sigsq'] = np.asarray([np.mean(data.var(0))] * self.k)
        return super(GMM, self).fit(data, *args, **kwargs)


class CMM(MixtureModel):
    def __init__(self, k, ds):
        """d is a list containing the number of categories for each feature"""
        super(CMM, self).__init__(k)
        self.params['alpha'] = [np.random.dirichlet([1]*d, size=k) for d in ds]

    def e_step(self, data):
        raise NotImplementedError()

    def m_step(self, data, p_z):
        raise NotImplementedError()

        return {
            'pi': new_pi,
            'alpha': new_alpha,
        }

    @property
    def bic(self):
        raise NotImplementedError()
