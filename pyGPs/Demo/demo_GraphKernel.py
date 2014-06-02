#! /usr/bin/env python
#coding=utf-8

import numpy as np
from scipy.sparse.csc import csc_matrix
import pyGPs
from pyGPs.Validation import valid
from pyGPs.GraphExtension import graphUtil,graphKernels

location = 'data_for_demo/graphData/'
data = np.load(location+'MUTAG.npz')

# n = num of nodes
# N = num of graphs
# p = num of labels
A = csc_matrix( (data['adj_data'], data['adj_indice'], \
    data['adj_indptr']), shape=data['adj_shape'])     # n x n adjancy array (sparse matrix)  
gr_id = data['graph_ind']                             # n x 1 graph id array
node_label = data['responses']                        # n x 1 node label array
graph_label = data['labels']                          # N x 1 graph label array
N = graph_label.shape[0]                              # number of graphs)

graph_label = np.int8(graph_label)
for i in xrange(N):
    if graph_label[i,0] == 0:
        graph_label[i,0] -= 1

#===========================================================================
# COMPUTE PROPAGATION KERNELS
#===========================================================================
num_Iteration = 10
K = graphKernels.propagationKernel(A, node_label, gr_id, num_Iteration, 'label_propagation', SUM=True, VIS=False, showEachStep=True) 


#----------------------------------------------------------------------
# Cross Validation
#----------------------------------------------------------------------
ACC = []           # accuracy 

for t in xrange(num_Iteration+1):
    print 'number of kernel iteration(T) is', t
    Matrix = K[:,:,t]
            
    # start cross-validation for this T
    for index_train, index_test in valid.k_fold_index(N, K=10):
        
        y_train = graph_label[index_train,:]
        y_test  = graph_label[index_test,:]

        n1 = len(index_train)
        n2 = len(index_test)        
        
        model = pyGPs.GPC()
        M1,M2 = graphUtil.formKernelMatrix(Matrix, index_train, index_test)
        k = pyGPs.cov.Pre(M1,M2)
        model.setPrior(kernel=k)
        
        # gp
        x_train = np.zeros((n1,1)) 
        x_test = np.zeros((n2,1))       
        model.optimize(x_train, y_train)
        model.predict(x_test)
        
        # evaluation 
        predictive_class = np.sign(model.ym)
        acc = valid.ACC(predictive_class, y_test)   
        ACC.append(acc) 
    
    print 'Accuracy: ', np.round(np.mean(ACC),2), '('+str(np.round(np.std(ACC),2))+')'
        
