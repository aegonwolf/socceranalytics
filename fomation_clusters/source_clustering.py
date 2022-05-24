import numpy as np
import scipy
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from scipy.cluster.hierarchy import fcluster, dendrogram, linkage

def center_players_framemean(coords):
    # shift it such that the mean of all players is 0 at every point in time
    return coords - np.mean(coords, axis=1, keepdims=True)


def window_to_formation(coordinates):
    #TODO better normalization
    # for now we simply do no normalization
    coordinates = center_players_framemean(coordinates)
    mus = np.mean(coordinates, axis=0)
    covs = np.empty((11, 2, 2))
    for p in range(11):
        covs[p] = np.cov(coordinates[:,p,:].T)
    return (mus, covs)


def cluster_formations(dists, n_clusters, method='ward', plot=False): # change to scikit
    #Z = ward(sp.spatial.distance.squareform(dists))
    Z = linkage(scipy.spatial.distance.squareform(dists), method, optimal_ordering=True)
    assignment = fcluster(Z, n_clusters, criterion='maxclust')
    if plot:
        plt.figure(figsize=(16, 8)) 
        dendrogram(Z, no_labels=True, color_threshold=-1)
    return assignment


# Modified from: https://en.wikipedia.org/wiki/Ternary_search#Iterative_algorithm
def ternary_search_extended(f, left, right, absolute_precision):
    count = 0
    while abs(right - left) >= absolute_precision:
        left_third = left + (right - left) / 3
        right_third = right - (right - left) / 3

        count += 1
        f_left  = f(left_third)
        f_right = f(right_third)
        if f_left > f_right:
            left = left_third
        else:
            right = right_third
    
    # print(f'ternary search took {count} function evaluations')
    if f_left < f_right:
        return f_left, left
    else: 
        return f_right, right


def wasserstein_distance_vectorized(m1, m2, C1, C2):
    # https://de.wikipedia.org/wiki/Wasserstein-Metrik#Normalverteilung gives:
    # W^2 = ||m1-m2||^2 + Tr[C1] + Tr[C2] - 2Tr[Sqrt(C1C2)]
    C1C2 = np.matmul(C1, C2)
    a = C1C2[:,:,0,0]
    b = C1C2[:,:,0,1]
    c = C1C2[:,:,1,0]
    d = C1C2[:,:,1,1]
    t1 = 0.5*(a + d)
    t2 = (0.25*(a - d)**2 + b*c)**0.5
    return np.maximum(0, np.sum((m1-m2)**2, axis=-1) + C1[:,:,0,0] + C1[:,:,1,1] + C2[:,:,0,0] + C2[:,:,1,1] - 2*((t1+t2)**0.5 + (t1-t2)**0.5))**0.5


def formation_distance_extended_vectorized(a, b):    
    mu_a, cov_a = a
    mu_b, cov_b = b
    # move them such that the center of mass is at the center
    mu_a = mu_a - np.mean(mu_a, axis=0)
    mu_b = mu_b - np.mean(mu_b, axis=0)
    
    # arrange them such that we can compute the wasserstein distance in a vectorized way
    mus_a = np.transpose(np.tile(mu_a, (11, 1, 1)), [1, 0, 2])
    covs_a = np.transpose(np.tile(cov_a, (11, 1, 1, 1)), [1, 0, 2, 3])
    mus_b = np.tile(mu_b, (11, 1, 1))
    covs_b = np.tile(cov_b, (11, 1, 1, 1))
    
    # define the distance depending on the scale factor k
    # since it is a ratio, the range is symmetric if we give it log(k)
    def dist_extended(log_k, return_assignments=False):
        k = 2**log_k
        # Find the player correspondences
        W = wasserstein_distance_vectorized(k*mus_a, 1/k*mus_b, k**2*covs_a, 1/k**2*covs_b)
        
        row_ind, col_ind = linear_sum_assignment(W)
        if return_assignments:
            return row_ind, col_ind
        else: 
            return W[row_ind, col_ind].sum()
    
    # the method looks pretty unimodal so i think applying ternary search is ok
    # return ternary_search(dist, -1, 1, 0.001) # naive method has a precision of 0.02
    # for speed-up
    min_dist, argmin_k = ternary_search_extended(dist_extended, -0.3, 0.3, 0.05)
    min_row_ind, min_col_ind = dist_extended(argmin_k, return_assignments=True)

    return min_dist, argmin_k, min_row_ind, min_col_ind


def compute_distance_matrix_extended(formations):
    n = len(formations)
    k_matrix = np.zeros((n,n))
    row_col_matrix = []
    dists = np.zeros((n, n))

    for i in range(n):
        row_cols_col = []
        for j in range(i+1,n):
            d, k, row_ass, col_ass = formation_distance_extended_vectorized(formations[i], formations[j])
            k_matrix[i][j] = k
            k_matrix[j][i] = k
            row_cols_col.append([row_ass, col_ass])
            dists[i][j] = d
            dists[j][i] = d
        row_col_matrix.append(row_cols_col)
        
    return dists, k_matrix, row_col_matrix