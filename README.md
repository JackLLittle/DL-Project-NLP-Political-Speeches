Project Purpose: 
To work to build a model that can identify Trump speech patterns and correctly classify them as his or not.

I found this topic to be interesting because there seems to be a disconnect in the US about charismatic speech and how certain phrases which lack the typical political nuance generate significantly more appraise from certain populations. Identifying key factors in what identifies these speeches given by Trump and thereby being able to classify whether a piece of speech is Trump’s or not would help to potentially isolate why there is such a significant difference in the effectiveness of his persuasion despite the general disdain for his policies among US citizens. 

Dataset: 
The dataset was taken from a precompiled set of speeches from the 2020 election cycle found at the following github link: https://github.com/ichalkiad/datadescriptor_uselections2020
These speeches are labeled based on the deliver of the speech and then this was encoded to be given by Trump or not.
The data itself was compiled from
1. the Miller Center of the University of Virginia (https://millercenter.org/);
2. Vote Smart (https://justfacts.votesmart.org/), a non-profit, non-partisan research organization for the collection of information about candidates for public office in the US;
3. the Cable-Satellite Public Affairs Network (C-SPAN, https://www.c-span.org/), which maintains an archive of televised public campaign speeches;
4. for the speeches and statements of the Democrats' ticket for the 2020 elections, data were also collected from their personal Medium blogs (https://kamalaharris.medium.com/, https://medium.com/@JoeBiden).

Source: Chalkiadakis, I., Anglès d'Auriac, L., Peters, G., & Frau-Meigs, D. (2025). A text dataset of campaign speeches of the main tickets in the 2020 US presidential election [Data set]. Zenodo. https://doi.org/10.5281/zenodo.14785782.

Example of the data:
<img width="1736" height="79" alt="image" src="https://github.com/user-attachments/assets/427e9cb9-7a6b-4a6b-9d52-14573def7c4d" />

Model:
I built a binary classifier on top of the base RoBERTa model from Huggingface

Training the Model: 
Start by installing the package likely in a virtual environment using "pip install -e ."
Next after the directories are correctly setup with access to the data and the virtual environment succesfully initialized, the model can be trained by doing the following:

The following line removes the previously trained model and should be run before retraining not from a checkpoint.
rm -rf outputs/roberta_trump

This section of code should be pasted all at once and will train the model with the passed parameters into your commandline to train the model.

python train_models.py \
  --batch-size 8 \
  --epochs 4 \
  --learning-rate 2e-5 \
  --weight-decay 0.01 \
  --patience 2 \
  --save-dir outputs/roberta_trump

  Note: This model was very easy to overfit to the extreme to the point of consistent 100% accuracy at 5 or more epochs

Results:
The metrics I used to test my model were primarily the basic trio of accuracy, precision, recall and their composite f1 as well as AUC score. 
I used these because the end goal of this project was a binary classification problem. 
For all these the model scored quite well indicating that Trump has a particularly distinct speech pattern which made it so that the model had quite a high results in all of the stats.
accuracy: 0.9298245614035088,
precision: 0.9230769230769231,
recall: 0.9230769230769231,
f1: 0.9230769230769231,
auc: 0.9913151364764269
<img width="1089" height="390" alt="image" src="https://github.com/user-attachments/assets/5021e869-aaa6-4c78-a9f1-15f3eb83ee79" />


Limitations:
The primary limitation of this model was likely the dataset. The distinct nature of the speeches made the model extremely prone to overfitting and as such having a model that would likely not generalize across different timeframes. Unfortunately, I did not have time to do validation across differing datasets and if so I would imagine the model would see slightly different results especially given that speech patterns change drastically over time. Also because the dataset is primarily comprised of those made during the 2020 election cycle the model may have some confounding variables surrounding political language such as conservative vs. liberal which is not fully accounted for due to the restrained nature of the dataset. With more time that is something I would likely revisit to test the model further. 

Additional testing could also have been checking for speech patterns across mediums where there is a significant tonal change which would likely have added significant additional noise to the model but also allowed for it to better pick up distinct signals of his speech patterns as a whole. 
