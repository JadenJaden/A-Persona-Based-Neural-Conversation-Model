import argparse

import torch

from data_preprocess import Data_Preprocess
from embedding_google import Get_Embedding
from encoder_rnn import Encoder_RNN
from decoder_rnn import Decoder_RNN
from train_network import Train_Network
from run_iterations import Run_Iterations

use_cuda = torch.cuda.is_available()

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num_iters", type=int, help="Number of iterations over the training set.", default=10)
    parser.add_argument("-nl", "--num_layers", type=int, help="Number of layers in Encoder and Decoder", default=3)
    parser.add_argument("-z", "--hidden_size", type=int, help="GRU Hidden State Size", default=1024)
    parser.add_argument("-b", "--batch_size", type=int, help="Batch Size", default=32)
    parser.add_argument("-lr", "--learning_rate", type=float, help="Learning rate of optimiser.", default=0.001)

    parser.add_argument("-l", "--max_length", type=int, help="Maximum Sentence Length.", default=20)
    parser.add_argument("-tp", "--tracking_pair", type=bool, help="Track change in outputs over a randomly chosen sample.", default=False)
    parser.add_argument("-d", "--dataset", type=str, help="Dataset directory.", default='../Datasets/OpenSubtitles/')
    parser.add_argument("-e", "--embedding_file", type=str, help="File containing word embeddings.", default='../../Embeddings/GoogleNews/GoogleNews-vectors-negative300.bin.gz')

    args = parser.parse_args()

    num_iters = args.num_iters
    num_layers = args.num_layers
    hidden_size = args.hidden_size
    batch_size = args.batch_size
    learning_rate = args.learning_rate
    max_length = args.max_length
    tracking_pair = args.tracking_pair
    dataset = args.dataset
    embedding_file = args.embedding_file

    print('Model Parameters:')
    print('Hidden Size                :', hidden_size)
    print('Batch Size                 :', batch_size)
    print('Number of Layers           :', num_layers)
    print('Max. input length          :', max_length)
    print('Learning rate                :', learning_rate)
    print('--------------------------------------\n')

    print('Reading input data.')
    data_preprocess = Data_Preprocess(dataset, max_length=max_length)

    train_in_seq = data_preprocess.x_train
    train_out_seq = data_preprocess.y_train
    train_lengths = data_preprocess.lengths_train

    dev_in_seq = data_preprocess.x_val
    dev_out_seq = data_preprocess.y_val
    dev_lengths = data_preprocess.lengths_val

    word2index = data_preprocess.word2index
    index2word = data_preprocess.index2word
    word2count = data_preprocess.word2count
    vocab_size = data_preprocess.vocab_size

    print("Number of training Samples  :", len(train_in_seq))
    print("Number of validation Samples  :", len(dev_in_seq))

    print('Creating Word Embedding.')

    ''' Use pre-trained word embeddings '''
    embedding = Get_Embedding(word2index, word2count, embedding_file)

    encoder = Encoder_RNN(hidden_size, embedding.embedding_matrix, batch_size=batch_size,
                          num_layers=num_layers, use_embedding=True, train_embedding=False)
    decoder = Decoder_RNN(hidden_size, embedding.embedding_matrix, num_layers=num_layers,
                          use_embedding=True, train_embedding=False, dropout_p=0.1)

    if use_cuda:
        encoder = encoder.cuda()
        decoder = decoder.cuda()

    print("Training Network.")

    train_network = Train_Network(encoder, decoder, index2word, num_layers=num_layers)

    run_iterations = Run_Iterations(train_network, train_in_seq, train_out_seq, train_lengths, index2word,
                                    batch_size, num_iters, learning_rate, tracking_pair=tracking_pair,
                                    dev_in_seq=dev_in_seq, dev_out_seq=dev_out_seq, dev_input_lengths=dev_lengths)
    run_iterations.train_iters()
    run_iterations.evaluate_randomly()
