import pandas as pd
import numpy as np
import datetime
import argparse
from sklearn.metrics import silhouette_score

from source_preprocessing import *
from source_clustering import *
from source_plotting import * 

if __name__ == '__main__':

    path = 'data/tracab/Italy v Wales.xml'

    print('Loading Match...')
    df = load_data(path)
    breaks = df['time'][(df['time'] - df['time'].shift()) > datetime.timedelta(0, 0, 40000)]

    # flip player coordinates at halftime, make players play in the same direction
    df_players = correct_player_cordinates(df, breaks)

    # define ball possession phases
    possession_phases = df.ball_possession[df.ball_possession != df.ball_possession.shift()]
    phase_lengths = np.roll(possession_phases.index.values, shift=-1) - possession_phases.index.values
    phase_lengths[-1] = df.ball_possession.index[-1] - possession_phases.index[-1] # correct for roll
    phases = pd.DataFrame({'possession': possession_phases.values, 'phase_length': phase_lengths},index=possession_phases.index)
    ball_possessions: pd.Series = df['ball_possession'] # raw ball possession information

    # get 1-minute aggregate possession windows
    print('Getting Formation Windows...')
    windows_coords = get_sg_window_coords(df, df_players, phases, ball_possessions, breaks)

    windows_formations = {key: list(map(window_to_formation, windows_coords[key])) 
                            for key in windows_coords.keys()}
    dist_matrices = {key: compute_distance_matrix_extended(windows_formations[key])[0] 
                        for key in windows_formations.keys()} # index 0 is the distance matrix
    dict_rowcols = {key: compute_distance_matrix_extended(windows_formations[key])[2]
                        for key in windows_formations.keys()}

    print('Clustering...')
    # cluster graphs
    clusterings = []
    scores = []
    k_list = [2, 3, 4]
    for k in k_list:
        clustering = [cluster_formations(dist_matrices[key], n_clusters=k, method='ward', plot=False) 
                    for key in dist_matrices.keys()]
        clustering = [cl - 1 for cl in clustering] # make cluster numbering start with 0 instead of 1. 
        clusterings.append(clustering)
        score = [silhouette_score(dist_matrices[key]+dist_matrices[key].T, clustering[ct], metric="precomputed") 
                for ct, key in enumerate(dist_matrices.keys())]
        scores.append(score)
    formation_cluster_lists = {key: clusterings[np.argmax(scores, axis=0)[ct]][ct] for ct, key in enumerate(dist_matrices.keys())}

    N_CLUSTERS = k_list[np.argmax(np.mean(scores, axis=1))]
    for key, maxscore_ind in zip(['team_1_offensive', 'team_1_defensive', 'team_2_offensive', 'team_2_defensive'], np.argmax(scores, axis=0)):
        N_CLUSTERS = k_list[maxscore_ind]
        clustering = formation_cluster_lists[key]
        all_formations = windows_formations[key]
        rowcols = dict_rowcols[key]

        # reorder the cluster assignments such that the largest ones come first
        cluster_sizes = np.bincount(clustering, minlength=N_CLUSTERS+1)[1:]
        # for each cluster, find where it has to go
        substitutions = np.argsort(np.argsort(-cluster_sizes)) # compute the rank of each cluster to map it to this index
        for i in range(len(clustering)):
            clustering[i] = substitutions[clustering[i]-1]+1
        # Warn from singleton clusters
        if (clustering == N_CLUSTERS).sum() == 1:
            print('WARNING: There are singleton clusters')

        # this is for filling the matrix of Wasserstein-Assignments, such that indices are easy
        def fill_matrix(a):
            filled_a = []
            for item in a:
                fill_length = len(a[0]) + 1 - len(item)
                filled_a.append([None]*fill_length + item)
            return filled_a

        rowcols_filled = fill_matrix(rowcols)
        all_means_centered = []

        for formation in all_formations:
            COM = np.mean(formation[0], axis=0)
            all_means_centered.append(formation[0] - COM)
        # find indices of formations grouped by cluster
        clusters_idx = []
        for ind in range(1, N_CLUSTERS+1):
            clusters_idx.append([i[0] for i in enumerate(clustering) if i[1] == ind])

        # reorder the players according to their formation assignments for plotting only
        formation_clusters_ordered = []
        for cluster_nr in range(len(clusters_idx)):
            wasserstein_assignments = [[np.arange(11), np.arange(11)]]

            for index in range(1, len(clusters_idx[cluster_nr])):
                wasserstein_assignments.append(rowcols_filled[clusters_idx[cluster_nr][0]][clusters_idx[cluster_nr][index]])

            clfo_arr, formations_ordered = [], []
            for form_index in range(len(wasserstein_assignments)):
                clfo_ordered =  []
                clfo_arr = all_means_centered[clusters_idx[cluster_nr][form_index]]
                index_array = list(wasserstein_assignments[form_index][1])
                for i in index_array:
                    clfo_ordered.append(clfo_arr[i])
                formations_ordered.append(clfo_ordered)
            formation_clusters_ordered.append(formations_ordered)

        # compute means and covariance for each cluster and put into the format for the plot_formation_cluster function
        means_cluster, cov_cluster, plot_clusters = [], [], []
        for cluster in formation_clusters_ordered:
            clustering_cov = []
            for position in range(11):
                position_clusters = np.array([formation[position] for formation in cluster]).T
                clustering_cov.append(np.cov(position_clusters))
            means_cluster.append(np.mean(cluster, axis=0))
            cov_cluster.append(clustering_cov)
        for cluster in range(len(means_cluster)):
            plot_clusters.append([np.array(means_cluster[cluster]), np.array(cov_cluster[cluster])])
        
        # plotting
        for cluster_index in range(N_CLUSTERS):
            fig = plt.figure(figsize=(8, 8))
            ax = plt.gca()
            ax.set_xlim(-30, 30)
            ax.set_ylim(-30, 50)
            ax.axis('off')
            
            for i in range(len(clusters_idx[cluster_index])):
                plot_cluster(np.array(formation_clusters_ordered[cluster_index][i]), fig, ax, True)
            plt.title(get_fig_title(key, cluster_index+1))
            plt.savefig(f"assets/Prototypes_Points_{key}_Cluster_{cluster_index + 1}", facecolor='white', transparent=False)
            # plt.show()

        for i in range(len(clusters_idx)):
            # print('----------')
            # players = active_players[f'team{clustering_name[0]}_{clustering_name[1:]}_{i+1}']
            plot_formation_cluster_compact([means_cluster[i], cov_cluster[i]])
            plt.title(get_fig_title(key, i+1))
            plt.savefig(f"assets/Prototypes_coloredellipse_{key}_Cluster_{i+ 1}.png", facecolor='white', transparent=False)
            # print(f"{key} Cluster with index {i+1}")
            # plt.show()

    print('Done.')
