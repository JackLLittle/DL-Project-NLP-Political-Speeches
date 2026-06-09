Project Purpose: 
To work to build a model that can identify Trump speech patterns and correctly classify them as his or not.

I found this topic to be interesting because there seems to be a disconnect in the US about charismatic speech and how certain phrases which lack the typical political nuance generate significantly more appraise from certain populations. Identifying key factors in what identifies these speeches given by Trump and thereby being able to classify whether a piece of speech is Trump’s or not would help to potentially isolate why there is such a significant difference in the effectiveness of his persuasion despite the general disdain for his policies among US citizens. 

Dataset: 
The dataset was taken from a precompiled set of speeches from the 2020 election cycle found at the following github link: https://github.com/ichalkiad/datadescriptor_uselections2020

Training the Model: 
Start by installing the package likely in a virtual environment using "pip install -e ."
Next after the directories are correctly setup with access to the data and the virtual environment succesfully initialized run the model can be trained by doing the following:

The following line removes the previously trained model and should be run before retraining not from a checkpoint.
rm -rf outputs/roberta_trump

This section of code should be pasted all at once and will train the model with the passed parameters into your commandline to train the model
python train_models.py \
  --batch-size 8 \
  --epochs 4 \
  --learning-rate 2e-5 \
  --weight-decay 0.01 \
  --patience 2 \
  --save-dir outputs/roberta_trump

  Note: This model was very easy to overfit to the extreme to the point of consistent 100% accuracy at 5 or more epochs

  Results:
