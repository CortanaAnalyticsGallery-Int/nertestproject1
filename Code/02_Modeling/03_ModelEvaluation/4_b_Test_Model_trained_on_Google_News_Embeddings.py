
# coding: utf-8

# ## Testing the Neural Entity Detector trained using Google News Word Embeddings

# #### Download Google News vectors from <a href = "https://drive.google.com/file/d/0B7XkCwpI5KDYNlNUTTlSS21pQmM/edit"> here</a>
# #### Extract and move them

# In[1]:

get_ipython().system(u'cp "Location of the vectors" .')


# In[ ]:

get_ipython().system(u'mkdir Drugs_and_Diseases')
get_ipython().system(u'cp "Location of train.txt" Drugs_and_Diseases')
get_ipython().system(u'cp "Location of test.txt" Drugs_and_Diseases')
get_ipython().system(u'cp "Location of evaluation script" Drugs_and_Diseases')
get_ipython().system(u'chmod 777 Drugs_and_Diseases/evalD_a_D.pl')


# In[1]:

get_ipython().run_cell_magic(u'writefile', u'Data_Preparation.py', u'from keras.preprocessing import sequence\nimport numpy as np\nimport cPickle as cpickle\nimport gensim\n\nclass Data_Preparation:\n\n    def __init__ (self, classes, seq_length, train_file=None, test_file=None, vector_size = 100):\n        \n        # Some constants\n        self.DEFAULT_N_CLASSES = classes#3\n        self.DEFAULT_N_FEATURES = vector_size\n        self.DEFAULT_MAX_SEQ_LENGTH = seq_length#213\n        \n        # Other stuff\n        self.wordvecs = None\n        self.word_to_ix_map = {}\n        self.n_features = 0\n        self.n_tag_classes = 0\n        self.n_sentences_all = 0\n        self.tag_vector_map = {}\n        \n        self.max_sentence_len_train = 0\n        self.max_sentence_len_test = 0\n        self.max_sentence_len = 0\n        \n        self.all_X_train = []\n        self.all_Y_train = []\n        self.all_X_test = []\n        self.all_Y_test = []\n        self.unk_words = []\n        \n        if train_file and test_file:\n            self.read_and_parse_data(train_file, test_file)\n            \n    def get_data (self):\n        return (self.all_X_train, self.all_Y_train, self.all_X_test, self.all_Y_test, self.wordvecs)\n    \n    def decode_prediction_sequence (self, pred_seq):\n        \n        pred_tags = []\n        for class_prs in pred_seq:\n            class_vec = np.zeros(self.DEFAULT_N_CLASSES, dtype=np.int32)\n            class_vec[np.argmax(class_prs)] = 1\n            if tuple(class_vec.tolist()) in self.tag_vector_map:\n                pred_tags.append(self.tag_vector_map[tuple(class_vec.tolist())])\n            else:\n                print tuple(class_vec.tolist())\n        return pred_tags\n    \n    def read_and_parse_data (self, train_file, test_file, skip_unknown_words = False):\n        \n        print train_file, test_file\n        print("Loading W2V model")\n        W2V_model = gensim.models.KeyedVectors.load_word2vec_format(\'/home/akshay/notebooks/NER/GoogleNews-vectors-negative300.bin\', binary=True)\n        vocab = list(W2V_model.vocab.keys())\n        \n        self.word_to_ix_map = {}\n        self.wordvecs = []\n        \n        print("Creating LookUp table")\n        for index, word in enumerate(vocab):\n            self.word_to_ix_map[word] = index\n            self.wordvecs.append(W2V_model[vocab[index]])\n        \n        self.wordvecs = np.array(self.wordvecs)\n        \n        self.n_features = len(self.wordvecs[0])\n        print(self.n_features)\n        \n        # Add a zero vector for the Paddings\n        self.wordvecs = np.vstack((self.wordvecs, np.zeros(self.DEFAULT_N_FEATURES)))\n        zero_vec_pos = self.wordvecs.shape[0] - 1\n        \n        ##########################  READ TRAINING DATA  ######################### \n        with open(train_file, \'r\') as f_train:\n            \n            self.n_tag_classes = self.DEFAULT_N_CLASSES\n            self.tag_vector_map = {}    # For storing one hot vector notation for each Tag\n            tag_class_id = 0            # Used to put 1 in the one hot vector notation\n            raw_data_train = []\n            raw_words_train = []\n            raw_tags_train = []        \n\n            # Process all lines in the file\n            for line in f_train:\n                line = line.strip()\n                if not line:\n                    raw_data_train.append( (tuple(raw_words_train), tuple(raw_tags_train)))\n                    raw_words_train = []\n                    raw_tags_train = []\n                    continue\n                \n                word, tag = line.split(\'\\t\')\n                \n                raw_words_train.append(word)\n                raw_tags_train.append(tag)\n                \n                if tag not in self.tag_vector_map:\n                    one_hot_vec = np.zeros(self.DEFAULT_N_CLASSES, dtype=np.int32)\n                    one_hot_vec[tag_class_id] = 1\n                    self.tag_vector_map[tag] = tuple(one_hot_vec)\n                    self.tag_vector_map[tuple(one_hot_vec)] = tag\n                    tag_class_id += 1\n                    \n        print("raw_nd = " + str(len(raw_data_train)))\n        \n        #Adding a None Tag\n        one_hot_vec = np.zeros(self.DEFAULT_N_CLASSES, dtype = np.int32)\n        one_hot_vec[tag_class_id] = 1\n        self.tag_vector_map[\'NONE\'] = tuple(one_hot_vec)\n        self.tag_vector_map[tuple(one_hot_vec)] = \'NONE\'\n        tag_class_id += 1\n        \n        self.n_sentences_all = len(raw_data_train)\n\n        # Find the maximum sequence length for Training data\n        self.max_sentence_len_train = 0\n        for seq in raw_data_train:\n            if len(seq[0]) > self.max_sentence_len_train:\n                self.max_sentence_len_train = len(seq[0])\n                \n                \n        ##########################  READ TEST DATA  ######################### \n        with open(test_file, \'r\') as f_test:\n            \n            self.n_tag_classes = self.DEFAULT_N_CLASSES\n            tag_class_id = 0 \n            raw_data_test = []\n            raw_words_test = []\n            raw_tags_test = []        \n\n            # Process all lines in the file\n            for line in f_test:\n                line = line.strip()\n                if not line:\n                    raw_data_test.append( (tuple(raw_words_test), tuple(raw_tags_test)))\n                    raw_words_test = []\n                    raw_tags_test = []\n                    continue\n                \n                word, tag = line.split(\'\\t\') \n                \n                if tag not in self.tag_vector_map:\n                    print "added"\n                    one_hot_vec = np.zeros(self.DEFAULT_N_CLASSES, dtype=np.int32)\n                    one_hot_vec[tag_class_id] = 1\n                    self.tag_vector_map[tag] = tuple(one_hot_vec)\n                    self.tag_vector_map[tuple(one_hot_vec)] = tag\n                    tag_class_id += 1\n                \n                raw_words_test.append(word)\n                raw_tags_test.append(tag)\n                \n                                    \n        print("raw_nd = " + str(len(raw_data_test)))\n        self.n_sentences_all = len(raw_data_test)\n\n        # Find the maximum sequence length for Test Data\n        self.max_sentence_len_test = 0\n        for seq in raw_data_test:\n            if len(seq[0]) > self.max_sentence_len_test:\n                self.max_sentence_len_test = len(seq[0])\n                \n        #Find the maximum sequence length in both training and Testing dataset\n        self.max_sentence_len = max(self.max_sentence_len_train, self.max_sentence_len_test)\n        \n        ############## Create Train Vectors################\n        self.all_X_train, self.all_Y_train = [], []\n        \n        self.unk_words = []\n        count = 0\n        for word_seq, tag_seq in raw_data_train:  \n            \n            elem_wordvecs, elem_tags = [], []            \n            for ix in range(len(word_seq)):\n                w = word_seq[ix]\n                t = tag_seq[ix]\n                w = w.lower()\n                if w in self.word_to_ix_map :\n                    count += 1\n                    elem_wordvecs.append(self.word_to_ix_map[w])\n                    elem_tags.append(self.tag_vector_map[t])\n\n                elif "UNK" in self.word_to_ix_map :\n                    elem_wordvecs.append(self.word_to_ix_map["UNK"])\n                    elem_tags.append(self.tag_vector_map[t])\n                \n                else:\n                    w = "UNK"       \n                    new_wv = 2 * np.random.randn(self.DEFAULT_N_FEATURES) - 1 # sample from normal distribution\n                    norm_const = np.linalg.norm(new_wv)\n                    new_wv /= norm_const\n                    self.wordvecs = np.vstack((self.wordvecs, new_wv))\n                    self.word_to_ix_map[w] = self.wordvecs.shape[0] - 1\n                    elem_wordvecs.append(self.word_to_ix_map[w])\n                    elem_tags.append(list(self.tag_vector_map[t]))\n\n            \n            # Pad the sequences for missing entries to make them all the same length\n            nil_X = zero_vec_pos\n            nil_Y = np.array(self.tag_vector_map[\'NONE\'])\n            pad_length = self.max_sentence_len - len(elem_wordvecs)\n            self.all_X_train.append( ((pad_length)*[nil_X]) + elem_wordvecs)\n            self.all_Y_train.append( ((pad_length)*[nil_Y]) + elem_tags)\n\n        self.all_X_train = np.array(self.all_X_train)\n        self.all_Y_train = np.array(self.all_Y_train)\n        \n        ########################Create TEST Vectors##########################\n\n        self.all_X_test, self.all_Y_test = [], []\n        \n        for word_seq, tag_seq in raw_data_test:  \n            \n            elem_wordvecs, elem_tags = [], []            \n            for ix in range(len(word_seq)):\n                w = word_seq[ix]\n                t = tag_seq[ix]\n                w = w.lower()\n                if w in self.word_to_ix_map:\n                    count += 1\n                    elem_wordvecs.append(self.word_to_ix_map[w])\n                    elem_tags.append(self.tag_vector_map[t])\n                    \n                elif "UNK" in self.word_to_ix_map :\n                    self.unk_words.append(w)\n                    elem_wordvecs.append(self.word_to_ix_map["UNK"])\n                    elem_tags.append(self.tag_vector_map[t])\n                    \n                else:\n                    self.unk_words.append(w)\n                    w = "UNK"\n                    self.word_to_ix_map[w] = self.wordvecs.shape[0] - 1\n                    elem_wordvecs.append(self.word_to_ix_map[w])\n                    elem_tags.append(self.tag_vector_map[t])\n                \n            # Pad the sequences for missing entries to make them all the same length\n            nil_X = zero_vec_pos\n            nil_Y = np.array(self.tag_vector_map[\'NONE\'])\n            pad_length = self.max_sentence_len - len(elem_wordvecs)\n            self.all_X_test.append( ((pad_length)*[nil_X]) + elem_wordvecs)\n            self.all_Y_test.append( ((pad_length)*[nil_Y]) + elem_tags)\n\n        self.all_X_test = np.array(self.all_X_test)\n        self.all_Y_test = np.array(self.all_Y_test)\n        \n        print("UNK WORD COUNT " + str(len(self.unk_words)))\n        print("Found WORDS COUNT " + str(count))\n        print("TOTAL WORDS " + str(count+len(self.unk_words)))\n\n\n        return (self.all_X_train, self.all_Y_train, self.all_X_test, self.all_Y_test, self.wordvecs)\n ')


# In[2]:

get_ipython().run_cell_magic(u'writefile', u'NER_Model.py', u'from keras.preprocessing import sequence\nfrom keras.models import load_model\nfrom keras.models import Sequential\nfrom keras.layers import Dense, Embedding\nfrom keras.layers import LSTM\nfrom keras.layers import GRU\nfrom keras.layers.core import Activation\nfrom keras.regularizers import l2\nfrom keras.layers.wrappers import TimeDistributed\nfrom keras.layers.wrappers import Bidirectional\nfrom keras.layers.normalization import BatchNormalization\nfrom keras.layers.core import Dropout\nimport numpy as np\nimport pandas as pd\nimport sys\nimport keras.backend as K\nimport Data_Preparation\nfrom sklearn.metrics import confusion_matrix, classification_report\n\n# For reproducibility\nnp.random.seed(42)\n\nclass NER_Model:\n    """"""\n    def __init__ (self, reader):\n        \n        self.reader = reader\n        self.model = None\n        self.all_X_train, self.all_Y_train, self.all_X_test, self.all_Y_test, self.wordvecs = reader.get_data()\n        self.train_X = self.all_X_train\n        self.train_Y = self.all_Y_train\n        \n        self.test_X = self.all_X_test\n        self.test_Y = self.all_Y_test\n        \n    def load (self, filepath):\n        self.model = load_model(filepath)\n        \n    def save (self, filepath):\n        self.model.save(filepath)\n\n    def print_summary (self):\n        print(self.model.summary())\n        \n    def train (self, test_split = 0.2, epochs = 1, batch = 50, dropout = 0.2, reg_alpha = 0.0, units = 150, layers = 1):\n        \n        self.train_X = self.all_X_train\n        self.train_Y = self.all_Y_train\n        \n        self.test_X = self.all_X_test\n        self.test_Y = self.all_Y_test\n\n        print("Data Shapes")\n        print(self.train_X.shape)\n        print(self.train_Y.shape)\n        print(self.test_X.shape)\n        print(self.test_Y.shape)\n        \n        dropout = 0.2\n\n        self.model = Sequential()        \n        self.model.add(Embedding(self.wordvecs.shape[0], self.wordvecs.shape[1], input_length = self.train_X.shape[1], \\\n                                 weights = [self.wordvecs], trainable = False))\n        \n        self.model.add(Bidirectional(LSTM(units, return_sequences = True)))\n        \n        self.model.add(Dropout(dropout))\n        \n        if layers > 1:\n            self.model.add(Bidirectional(LSTM(units, return_sequences=True)))\n            self.model.add(Dropout(dropout))\n            \n        self.model.add(TimeDistributed(Dense(self.train_Y.shape[2], activation=\'softmax\')))\n        \n        self.model.compile(loss=\'categorical_crossentropy\', optimizer=\'adam\')\n        print(self.model.summary())\n\n        self.model.fit(self.train_X, self.train_Y, epochs = epochs, batch_size = batch)\n        \n    def evaluate_1(self):\n        target = open("Google_Output.txt", \'w\')\n        predicted_tags= []\n        test_data_tags = []\n        ind = 0\n        for x,y in zip(self.test_X, self.test_Y):\n            tags = self.model.predict(np.array([x]), batch_size=1)[0]\n            pred_tags = self.reader.decode_prediction_sequence(tags)\n            test_tags = self.reader.decode_prediction_sequence(y)\n            ind += 1\n            ### To see Progress ###\n            if ind%500 == 0: \n                print("Sentence" + str(ind))\n\n            pred_tag_wo_none = []\n            test_tags_wo_none = []\n            \n            for index, test_tag in enumerate(test_tags):\n                if test_tag != "NONE":\n                    if pred_tags[index] == "B-Chemical":\n                        pred_tag_wo_none.append("B-Drug")\n                    elif pred_tags[index] == "I-Chemical":\n                        pred_tag_wo_none.append("I-Drug")\n                    elif pred_tags[index] == \'None\':\n                        pred_tag_wo_none.append(\'O\')\n                    else:\n                        pred_tag_wo_none.append(pred_tags[index])\n                        \n                    if test_tag == "B-Chemical":\n                        test_tags_wo_none.append("B-Drug")\n                    elif test_tag == "I-Chemical":\n                        test_tags_wo_none.append("I-Drug")\n                    else:                        \n                        test_tags_wo_none.append(test_tag)\n            \n            for wo in pred_tag_wo_none:\n                target.write(str(wo))\n                target.write("\\n")\n            target.write("\\n")\n            \n            for i,j in zip(pred_tags, test_tags):\n                if i != "NONE" and j != "NONE":\n                    test_data_tags.append(j)\n                    predicted_tags.append(i)\n\n        target.close()\n        \n        predicted_tags = np.array(predicted_tags)\n        test_data_tags = np.array(test_data_tags)\n        print(classification_report(test_data_tags, predicted_tags))\n\n        simple_conf_matrix = confusion_matrix(test_data_tags,predicted_tags)\n        all_tags = sorted(list(set(test_data_tags)))\n        conf_matrix = pd.DataFrame(columns = all_tags, index = all_tags)\n        for x,y in zip(simple_conf_matrix, all_tags):\n            conf_matrix[y] = x\n        conf_matrix = conf_matrix.transpose()\n        \n        return conf_matrix')


# ### Train and Evaluate the model

# In[ ]:

from Data_Preparation import Data_Preparation
from NER_Model import NER_Model
import cPickle as cp
import gensim
from keras.models import load_model
import numpy as np

TRAIN_FILEPATH = "Drugs_and_Diseases//train_out.txt"
TEST_FILEPATH = "Drugs_and_Diseases//test.txt"

vector_size = 300
classes = 7 + 1
seq_length = 613
layer_arg = 2
ep_arg = 10

if __name__ == "__main__":

    
    print("\n\n\nRunning on BIO-NLP data\n\n\n")
        
    # Read the data
    print("Initializing data...")
    reader = Data_Preparation(classes, seq_length, TRAIN_FILEPATH, TEST_FILEPATH, vector_size)
    
    
    X_train, Y_train, X_test, Y_test, wordvecs = reader.get_data()
    print(X_train.shape)
    print(Y_train.shape)
    print(X_test.shape)
    print(Y_test.shape)
    
    # Train the model
    print("Training model... epochs = {0}, layers = {1}".format(ep_arg, layer_arg))
    nermodel = NER_Model(reader)
    nermodel.train(epochs=ep_arg, layers=layer_arg)
    
    # Evaluate the model
    print("Evaluating model...")
    confusion_matrix = nermodel.evaluate_1()
    print confusion_matrix

    print("Done.") 


# In[4]:

file1 = open("Google_Output.txt")
file2 = open("Drugs_and_Diseases//test.txt")
target = open("Drugs_and_Diseases//eval2_g.txt", "w")

list1 = []
list2 = []

for line in file1:
    list1.append(line)
    
for line in file2:
    list2.append(line)
    
for ind, line in enumerate(list2):
    x = line.split("\t")
    if len(x) == 1:
        target.write("\n")
    else:
        target.write(x[0])
        target.write("\t")
        if list1[ind] == "NONE":
            target.write("O")
        else:
            target.write(list1[ind])
    ind += 1

file1.close()
file2.close()
target.close()


# In[5]:

get_ipython().system(u'./Drugs_and_Diseases/evalD_a_D.pl Drugs_and_Diseases/eval2_g.txt Drugs_and_Diseases/test.txt #with cross 10 epocs')

