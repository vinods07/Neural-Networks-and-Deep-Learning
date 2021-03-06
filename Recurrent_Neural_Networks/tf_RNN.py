"""
Implementation of a vanilla Recurrent Neural Network using TensorFlow.
"""

import tensorflow as tf
import numpy as np

def one_hot(size,pos):
    ans=np.zeros([size,1])
    ans[pos]=1
    return ans

def softmax(z):
    # Naive implementation - doesn't handle overflows
    return np.exp(z)/np.sum(np.exp(z))

def decay(min_learning_rate,max_learning_rate,frac):
    return max_learning_rate - (max_learning_rate-min_learning_rate)*frac

class tf_RNN:
    def __init__(
                    self,
                    input_size,
                    batch_size,
                    state_size,
                    bptt_steps,
                    activation=tf.tanh
                ):
        # Store arguments
        self._activation=activation
        self._batch_size=batch_size
        self._input_size=input_size
        self._bptt_steps=bptt_steps
        self._state_size=state_size

        # Construct the computational graph
        self.U=tf.Variable(tf.random_uniform([state_size,input_size],-1.0/np.sqrt(input_size),1.0/np.sqrt(input_size)))
        self.V=tf.Variable(tf.random_uniform([input_size,state_size],-1.0/np.sqrt(input_size),1.0/np.sqrt(input_size)))
        self.W=tf.Variable(tf.random_uniform([state_size,state_size],-1.0/np.sqrt(input_size),1.0/np.sqrt(input_size)))

        # Biases
        self.B1=tf.Variable(tf.zeros([state_size,1]))
        self.B2=tf.Variable(tf.zeros([input_size,1]))

        # Placeholders
        self.input=tf.placeholder(tf.int32,[self._bptt_steps,batch_size],name="Input")
        self.correct_output=tf.placeholder(tf.int32,[self._bptt_steps,batch_size],name="Output")
        self._initial_state=tf.placeholder(tf.float32,[state_size,batch_size],name="Initial_State")

        # Computations
        inp = tf.transpose(tf.one_hot(self.input[0],depth=self._input_size))
        self._state=activation(tf.matmul(self.U,inp)+tf.matmul(self.W,self._initial_state)+self.B1)
        self._output=tf.matmul(self.V,self._state)+self.B2
        self._loss=tf.nn.softmax_cross_entropy_with_logits(logits=self._output,labels=tf.transpose(tf.one_hot(self.correct_output[0],depth=self._input_size)),dim=0)
        # self._output = tf.nn.softmax(tf.matmul(self.V,self._state)+self.B2)
        # self._loss = tf.losses.log_loss(labels=tf.transpose(tf.one_hot(self.correct_output[0],depth=self._input_size)),predictions=self._output)

        for i in range(1,self._bptt_steps):
            inp = tf.transpose(tf.one_hot(self.input[i],depth=self._input_size))
            self._state=activation(tf.matmul(self.U,inp)+tf.matmul(self.W,self._state)+self.B1)
            self._output=tf.matmul(self.V,self._state)+self.B2
            self._loss+=tf.nn.softmax_cross_entropy_with_logits(logits=self._output,labels=tf.transpose(tf.one_hot(self.correct_output[i],depth=self._input_size)),dim=0)
            # self._output = tf.nn.softmax(tf.matmul(self.V,self._state)+self.B2)
            # self._loss += tf.losses.log_loss(labels=tf.transpose(tf.one_hot(self.correct_output[i],depth=self._input_size)),predictions=self._output)

        self._loss=tf.reduce_mean(self._loss)
        self._init=tf.global_variables_initializer()

    def train(self,input_data,output_data,learning_rate=1.0,n_epochs=30,factor=10):
        """
        Training data is contained in `input_data`, `output_data`.
        Both of these arrays have `batch_size` number of columns and arbitrary number of rows.
        For language modeling :
        Each element of these arrays is the index of a particular word from the vocabulary.

        `bptt_steps` is the number of steps upto which truncated BPTT will be applied.
        """
        I=input_data; O=output_data
        with tf.Session() as sess:
            sess.run(self._init)

            state = np.zeros([self._state_size,self._batch_size])
            for epoch_no in range(n_epochs):
                total_loss = 0.0
                cur_learning_rate = decay(learning_rate/factor,learning_rate,epoch_no/n_epochs)
                train = tf.train.GradientDescentOptimizer(learning_rate=cur_learning_rate).minimize(self._loss)
                print("Current learning rate = {0}".format(cur_learning_rate))
                for cntr in range(len(I)//self._bptt_steps):
                    _,state,curr_loss = sess.run([train,self._state,self._loss],feed_dict={self.input:I[cntr*self._bptt_steps:min(len(I),(cntr+1)*self._bptt_steps),:],self.correct_output:O[cntr*self._bptt_steps:min(len(I),(cntr+1)*self._bptt_steps),:],self._initial_state:state})
                    total_loss += curr_loss
                    print("Loss after epoch {0}, batch {1} = {2}".format(epoch_no+1,(cntr+1)*self._bptt_steps,curr_loss/self._bptt_steps))
                print("Average loss in epoch {0} = {1}".format(epoch_no+1,total_loss/len(I)))

    # def calc_output(self,inp,state):
    #     """
    #     Predicts the output for a given value of state and input.
    #     Returns a tuple (output, new_state)
    #     """
    #     assert(len(inp)==np.shape(self.U)[1])
    #     new_state = self._activation(np.dot(self.U,inp)+np.dot(self.W,state)+self.B1)
    #     return softmax(np.dot(self.V,new_state)+self.B2),new_state
    #
    # def predict(self,index_to_word):
    #     """ Function which returns a random string generated by the RNN for a randomly chosen initial word. """
    #     size_V = len(index_to_word)
    #     init_word_index = np.random.randint(size_V)
    #
    #     while index_to_word[init_word_index] == '<eos>':
    #         init_word_index = np.random.randint(size_V)
    #
    #     res=[]; init_state = np.zeros([self._state_size,1])
    #     next_word_index = init_word_index
    #     while index_to_word[next_word_index] is not '<eos>':
    #         res.append(next_word_index)
    #         output, new_state = self.calc_output(one_hot(size_V,next_word_index),init_state)
    #         next_word_index = np.argmax(output)
    #         init_state = new_state
    #
    #     # Convert `res` array to string
    #     res = [index_to_word[i] for i in res]
    #     return " ".join(res)
