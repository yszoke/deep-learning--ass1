import time
import operator
import numpy as np
from keras.utils import np_utils
from sklearn.model_selection import train_test_split
import tensorflow as tf
import matplotlib.pyplot as plt


def initialize_parameters(layer_dims):
    """
    :param layer_dims: an array of the dimensions of each layer in the network
    (layer 0 is the size of the flattened input, layer L is the output softmax)
    :return: a dictionary containing the initialized W and b parameters of
    each layer (W1…WL, b1…bL).
    """
    parameters = {}
    for current_layer in range(1, len(layer_dims)):
        parameters[current_layer] = [np.random.randn(layer_dims[current_layer],
                                                     layer_dims[current_layer - 1]) * np.sqrt(2 / layer_dims[current_layer]),
                                     np.zeros((layer_dims[current_layer], 1))]

    return parameters


def linear_forward(A, W, b):
    """
    Implement the linear part of a layer's forward propagation.
    :param A: the activations of the previous layer
    :param W:the weight matrix of the current layer (of shape
    [size of current layer, size of previous layer])
    :param b: the bias vector of the current layer
    (of shape [size of current layer, 1])
    :return:
    Z – the linear component of the activation function (i.e., the value before
    applying the non-linear function)
    linear_cache – a dictionary containing A, W, b
    (stored for making the backpropagation easier to compute)
    """
    Z = np.dot(W, A)
    return Z + b, (A, W, b)


def softmax(Z):
    """
    :param Z: the linear component of the activation function
    :return: A - the activations of the layer
    activation_cache – returns Z, which will be useful for the backpropagation
    """
    e_x = np.exp(np.subtract(Z, np.max(Z, axis=0)))
    return e_x / e_x.sum(axis=0), Z


def relu(Z):
    """
     :param Z: the linear component of the activation function
     :return: A - the activations of the layer
     activation_cache – returns Z, which will be useful for the backpropagation
     """
    A = np.maximum(0, Z)
    return A, Z


def linear_activation_forward(A_prev, W, B, activation, dropout):
    """
    Implement the forward propagation for the LINEAR->ACTIVATION layer
    :param A_prev: activations of the previous layer
    :param W: the weights matrix of the current layer
    :param B: the bias vector of the current layer
    :param activation: the activation function to be used
    (a string, either “softmax” or “relu”)
    :return:
    A – the activations of the current layer
    cache – a joint dictionary containing both linear_cache and activation_cache
    """
    Z, linear_cache = linear_forward(A_prev, W, B)
    if activation == 'relu':
        A, activation_cache = relu(Z)
        if dropout < 1:
            drop_matrix = np.random.rand(A.shape[0], A.shape[1])
            drop_matrix = (drop_matrix < dropout)
            A = np.multiply(A, drop_matrix)
            A = np.divide(A, dropout)
            dropout_cache = drop_matrix
            return A, [linear_cache, activation_cache, dropout_cache]
    elif activation == 'softmax':
        A, activation_cache = softmax(Z)
    return A, [linear_cache, activation_cache]


def L_model_forward(X, parameters, use_batchnorm, dropout):
    """
    Implement forward propagation for the [LINEAR->RELU]*(L-1)->LINEAR->SOFTMAX
    computation
    :param X: the data, numpy array of shape (input size, number of examples)
    :param parameters: the initialized W and b parameters of each layer
    :param use_batchnorm: a boolean flag used to determine whether to apply
    batchnorm after the activation (note that this option needs to be set to “false” in Section 3 and “true” in Section 4).
    :return:
    AL – the last post-activation value
    caches – a list of all the cache objects generated by the linear_forward function

    use linear_activation_forward function with relu activation function in an
    iterative way (iteration for each layer starting with the input layer X and
    ending with 1 layer before the last layer)
    for the last layer - use linear_activation_forward with softmax
    activation function.
    """
    num_of_layers = len(parameters)
    A = X
    cache_list = []
    for layer in range(1, num_of_layers):
        W = parameters[layer][0]
        B = parameters[layer][1]
        A_prev = A
        A, cache = linear_activation_forward(A_prev, W, B, 'relu', dropout)
        if use_batchnorm:
            A = apply_batchnorm(A)
        cache_list.append(cache)

    W = parameters[num_of_layers][0]
    B = parameters[num_of_layers][1]
    A_prev = A
    A, cache = linear_activation_forward(A_prev, W, B, 'softmax', dropout)
    cache_list.append(cache)
    return A, cache_list


def compute_cost(AL, Y):
    """
    Implement the cost function defined by equation.
    :param AL: probability vector corresponding to your label predictions,
    shape (num_of_classes, number of examples)
    :param Y: the labels vector (i.e. the ground truth).
    :return: cost – the cross-entropy cost.
    """

    n_classes = AL.shape[0]
    n_examples = AL.shape[1]

    cost = 0
    for ex in range(0, n_examples):
        for cl in range(0, n_classes):
            if Y[cl][ex] == 1:
                cost += 1 * np.log(AL[cl][ex])
    cost /= (-n_examples)
    return cost


def apply_batchnorm(A):
    """
    performs batchnorm on the received activation values of a given layer.
    :param A: the activation values of a given layer
    :return: NA - the normalized activation values, based on the formula
    learned in class
    """

    sum = np.sum(A, axis=1, keepdims=True)
    mean = sum / A.shape[1]
    var = np.sum(np.square(A-mean), axis=1, keepdims=True) / A.shape[1]
    epsilon = np.finfo(float).eps
    return np.divide(np.subtract(A, mean), np.sqrt(var+epsilon))


def Linear_backward(dZ, cache):
    """
    Implements the linear part of the backward propagation process for a
    single layer
    :param dZ: the gradient of the cost with respect to the linear output of
    the current layer (layer l)
    :param cache: tuple of values (A_prev, W, b) coming from the forward
    propagation in the current layer
    :return:
    dA_prev -- Gradient of the cost with respect to the activation (of the previous layer l-1), same shape as A_prev
    dW -- Gradient of the cost with respect to W (current layer l), same shape as W
    db -- Gradient of the cost with respect to b (current layer l), same shape as b
    """
    A_prev = cache[0]
    W = cache[1]
    neurons = cache[2].shape[0]
    samples = A_prev.shape[1]

    dW = np.dot(dZ, A_prev.T) / samples
    db = np.array([[np.sum(dZ[i]) / samples] for i in range(neurons)])
    dA_prev = np.dot(W.T, dZ)
    return dA_prev, dW, db


def linear_activation_backward(dA, cache, activation, dropout, dropout_cache):
    """
    Implements the backward propagation for the LINEAR->ACTIVATION layer. The
    function first computes dZ and then applies the linear_backward function.
    :param dA: post activation gradient of the current layer
    :param cache: contains both the linear cache and the activations cache
    :param activation: the activation function used (relu/softmax)
    :return:
    dA_prev – Gradient of the cost with respect to the activation (of the previous layer l-1), same shape as A_prev
    dW – Gradient of the cost with respect to W (current layer l), same shape as W
    db – Gradient of the cost with respect to b (current layer l), same shape as b
    """
    linear_cache = cache[0]
    activation_cache = cache[1]
    if activation == 'relu':
        dZ = relu_backward(dA, activation_cache)
        dA_prev, dW, db = Linear_backward(dZ, linear_cache)
    elif activation == 'softmax':
        Y = cache[2]
        dZ = softmax_backward(dA, Y)
        dA_prev, dW, db = Linear_backward(dZ, linear_cache)
    if dropout < 1 and bool(dropout_cache):
        dA_prev = np.multiply(dA_prev, dropout_cache.get("cache"))
        dA_prev = np.divide(dA_prev, dropout)

    return dA_prev, dW, db


def relu_backward(dA, activation_cache):
    """
    Implements backward propagation for a ReLU unit
    :param dA: the post-activation gradient
    :param activation_cache: contains Z (stored during the forward propagation)
    :return: gradient of the cost with respect to Z
    """
    dZ = np.array(dA, copy=True)
    dZ[activation_cache <= 0] = 0
    return dZ


def softmax_backward(dA, activation_cache):
    """
    Implements backward propagation for a softmax unit
    :param dA: the post-activation gradient
    :param activation_cache: contains Z (stored during the forward propagation)
    :return: dZ – gradient of the cost with respect to Z
    """
    return np.subtract(dA, activation_cache)


def L_model_backward(AL, Y, caches, dropout):
    """
    Implement the backward propagation process for the entire network.
    :param AL: - the probabilities vector, the output of the forward propagation
     (L_model_forward)
    :param Y: the true labels vector (the "ground truth" - true classifications)
    :param caches: list of caches containing for each layer:
    a) the linear cache;
    b) the activation cache
    :return:
    Grads - a dictionary with the gradients
             grads["dA" + str(l)] = ...
             grads["dW" + str(l)] = ...
             grads["db" + str(l)] = ...
    """
    grads = {}
    dropout_cache = {}
    layers = len(caches)
    if dropout < 1:
        dropout_cache = {'prob': dropout, 'cache': caches[layers-2][2]}

    last_cache_plus_Y = [i for i in caches[layers - 1]]
    last_cache_plus_Y.append(Y)
    dA_prev, dW, db = linear_activation_backward(AL, last_cache_plus_Y, "softmax", dropout, dropout_cache)
    grads["dA" + str(layers-1)] = dA_prev
    grads["dW" + str(layers)] = dW
    grads["db" + str(layers)] = db
    for l in reversed(range(layers-1)):
        if dropout < 1 and l - 2 > 0:
            dropout_cache = {'prob': dropout, 'cache': caches[l - 2][2]}
        else:
            dropout_cache = {}
        dA_prev, dW, db = linear_activation_backward(grads["dA" + str(l + 1)], caches[l], "relu", dropout, dropout_cache)
        grads["dA" + str(l)] = dA_prev
        grads["dW" + str(l+1)] = dW
        grads["db" + str(l+1)] = db

    return grads


def Update_parameters(parameters, grads, learning_rate):
    """
    Updates parameters using gradient descent
    :param parameters: a python dictionary containing the DNN architecture’s
    parameters
    :param grads: a python dictionary containing the gradients
    (generated by L_model_backward)
    :param learning_rate: the learning rate used to update the parameters
    (the “alpha”)
    :return: parameters – the updated values of the parameters object
    provided as input
    """
    for l in range(1, len(parameters)+1):
        parameters[l][0] = parameters[l][0] - (learning_rate * grads["dW" + str(l)])
        parameters[l][1] = parameters[l][1] - (learning_rate * grads["db" + str(l)])

    return parameters


def plot(train_results, val_results, title, y_label, batch_size, use_batchnorm, dropout):
    """
    :param train_results
    :param val_results
    :param title: title of the graph
    :param y_label
    :param batch_size
    :param use_batchnorm: True/False
    :param dropout: 0-1
    """
    plt.plot([i[0] for i in train_results], [i[1] for i in train_results], label=f'training {y_label}')
    plt.plot([i[0] for i in val_results], [i[1] for i in val_results], label=f'validation {y_label}')
    plt.title(f'{title}: batch size:{batch_size}, use batchnorm={use_batchnorm}, dropout={dropout}')
    plt.xlabel('Iterations')
    plt.ylabel(y_label)
    plt.legend()
    plt.show()


def L_layer_model(X, Y, layers_dims, learning_rate, num_iterations, batch_size, use_batchnorm, dropout):
    """
    Implements a L-layer neural network. All layers but the last should have the
    ReLU activation function, and the final layer will apply the softmax
    activation function. The size of the output layer should be equal to the
    number of labels in the data. Please select a batch size that enables your
    code to run well (i.e. no memory overflows while still running
    relatively fast).
    :param X: the input data, a numpy array of shape
    (height*width , number_of_examples)
    :param Y: the “real” labels of the data, a vector of shape
    (num_of_classes, number of examples)
    :param layers_dims: a list containing the dimensions of each layer,
    including the input
    :param learning_rate: the value to "jump" in every gradient decent iteration
    :param num_iterations: the total number of iteration.
    :param batch_size: the number of examples in a single training batch.
    :return:
    the parameters learnt by the system during the training
    (the same parameters that were updated in the update_parameters function).
    the values of the cost function (calculated by the compute_cost function).
    One value is to be saved after each 100 training iterations (e.g. 3000 iterations -> 30 values).
    """
    costs = []
    costs_val = []
    accuracy_train_list = []
    accuracy_val = []
    last_cost_val = 100
    parameters = initialize_parameters(layers_dims)
    X_train, X_val, y_train, y_val = train_test_split(X.T, Y.T, test_size=0.2, random_state=42)
    num_epochs = num_iterations
    iteration = 0
    for epoch in range(num_epochs):
        print(f'Epoch:{epoch}')
        for batch in range(int(len(y_train) / batch_size)):

            starting_sample = batch * batch_size
            ending_sample = starting_sample + batch_size
            A, cache_list = L_model_forward(X_train[starting_sample:ending_sample].T, parameters, use_batchnorm, dropout)

            grads = L_model_backward(A, y_train[
                                        starting_sample:ending_sample].T,
                                     cache_list, dropout)
            parameters = Update_parameters(parameters, grads, learning_rate)

            if iteration % 100 == 0:
                costs.append((iteration, compute_cost(A, y_train[starting_sample:ending_sample].T)))

                A_val, cache_list_val = L_model_forward(X_val.T, parameters, use_batchnorm, 1)
                cost_val = compute_cost(A_val, y_val.T)
                costs_val.append((iteration, cost_val))

                accuracy_train = Predict(X_train[starting_sample:ending_sample].T, y_train[starting_sample:ending_sample].T, parameters, use_batchnorm)
                accuracy_train_list.append((iteration, accuracy_train))

                accuracy = Predict(X_val.T, y_val.T, parameters, use_batchnorm)
                accuracy_val.append((iteration, accuracy))

                print(f"iteration {iteration}, cost_val {cost_val}, accuracy {accuracy}")
                if last_cost_val - cost_val < 0.0000000001 and iteration > 18000:
                    print(f"early stopping after {iteration}")
                    plot(costs, costs_val, "Train validation cost", "Cost", batch_size, use_batchnorm, dropout)
                    plot(accuracy_train_list, accuracy_val, "Train validation accuracy", "Accuracy", batch_size, use_batchnorm, dropout)
                    accuracy_final_train = Predict(X_train.T, y_train.T, parameters, use_batchnorm)
                    accuracy_final_val = Predict(X_val.T, y_val.T, parameters, use_batchnorm)
                    print(f"training accuracy: {accuracy_final_train}")
                    print(f"validation accuracy: {accuracy_final_val}")
                    return parameters, costs
                last_cost_val = cost_val
            iteration += 1
    plot(costs, costs_val, "Train validation cost", "Cost", batch_size, use_batchnorm, dropout)
    plot(accuracy_train_list, accuracy_val, "Train validation accuracy", "Accuracy", batch_size, use_batchnorm, dropout)

    return parameters, costs


def Predict(X, Y, parameters, use_batchnorm):
    """
    The function receives an input data and the true labels and calculates
    the accuracy of the trained neural network on the data.
    :param X: the input data, a numpy array of shape (height*width, number_of_examples)
    :param Y: the “real” labels of the data, a vector of shape
    (num_of_classes, number of examples)
    :param parameters: a python dictionary containing the DNN
    architecture’s parameters
    :return:
    accuracy – the accuracy measure of the neural net on the provided data
    (i.e. the percentage of the samples for which the correct label receives the
    highest confidence score). Use the softmax function to normalize the
    output values.
    """

    AL, caches = L_model_forward(X, parameters, use_batchnorm, 1)
    AL = softmax(AL)[0]
    acc = 0
    for i in range(AL.shape[1]):
        tmp_AL = max(enumerate(AL[:, i]), key=operator.itemgetter(1))[0]
        tmp_Y = max(enumerate(Y[:, i]), key=operator.itemgetter(1))[0]
        if tmp_AL == tmp_Y:
            acc += 1
    return (acc / Y.shape[1])*100


if __name__ == '__main__':
    data = tf.keras.datasets.mnist.load_data()
    (train_images, train_labels), (test_images, test_labels) = data
    train_labels = np_utils.to_categorical(train_labels, 10)
    test_labels = np_utils.to_categorical(test_labels, 10)
    layers = [784, 20, 7, 5, 10]
    learning_rate = 0.009
    num_iterations = 3000
    batch_size = 32
    use_batchnorm = False
    dropout = 1

    train_images_flat = train_images.reshape(train_images.shape[0], -1)
    test_images_flat = test_images.reshape(test_images.shape[0], -1)

    train_images_norm = np.divide(train_images_flat, 255)
    test_images_norm = np.divide(test_images_flat, 255)
    start_time = time.time()
    parameters, costs = L_layer_model(train_images_norm.T, train_labels.T, layers, learning_rate, num_iterations, batch_size, use_batchnorm, dropout)
    run_time = (time.time() - start_time) / 60
    run_time = "%.2f" % run_time
    print(f"run time: {run_time}")
    accuracy = Predict(test_images_norm.T, test_labels.T, parameters,
                       use_batchnorm)

    print(f"test accuracy: {accuracy}")

