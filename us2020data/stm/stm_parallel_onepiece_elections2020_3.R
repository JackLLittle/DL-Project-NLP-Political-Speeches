################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

require(dplyr)
require(lda)
require(slam)
require(stm)
require(tidytext)
require(ggplot2)
require(reshape2)
require(wordcloud)
require(huge)

dictionary <- "POTUS2020"
DIRtop <- sprintf("%s/us2020data/stm/postprocessed4stm/%s/stm/", getwd(), dictionary)
all_subdirectories <- list.dirs(DIRtop, full.names = FALSE, recursive = FALSE)
directory <- DIRtop
sage <- 0
for (use_content_variable in c(1)) {        
    for (time in c(1,0)){
        for (subdir in all_subdirectories){
            
            timeframe <- subdir
            use_time_variable <- time
            LDAbeta <- sage
            print(subdir)
            print(directory)
            print(timeframe)
            print(use_content_variable)
            print(use_time_variable)
            print(LDAbeta)
            
            
            topicnum <- c(10, 15, 20, 25)
            if (LDAbeta == 1){
                LDAbeta <- TRUE
            }else{
                LDAbeta <- FALSE
            }    
            DIR <- sprintf("%s/%s/", directory, timeframe)
            if (LDAbeta == FALSE){
                dir.create(file.path(DIR, "LDAbeta_false"), showWarnings = FALSE)
                DIR <- sprintf("%s/LDAbeta_false/", DIR)
            }
            if (use_time_variable == 1){
                dir.create(file.path(DIR, "time_covariate"), showWarnings = FALSE)
                DIR <- sprintf("%s/time_covariate/", DIR)
            }

            speeches <- read.csv(sprintf("%s/%s/data.csv", directory, timeframe), colClasses = c("character", 
                                                                                                "character",
                                                                                                "character", 
                                                                                                "list",                                                                                                 
                                                                                                "character", 
                                                                                                "character", 
                                                                                                "character",                                                                                                                                                                                        
                                                                                                "factor",
                                                                                                "integer",
                                                                                                "integer",
                                                                                                "character",
                                                                                                "character",
                                                                                                "character"                                                                                                
                                                                                                ))
            summary(speeches)
            
            tryCatch(
                {
                    load(sprintf("%s/%s/vocab.RData", directory, timeframe))
                    vocab <- vocab$vocab
                    load(sprintf("%s/%s/data_dtm.RData", directory, timeframe))
                    docs <- readCorpus(stmdocuments, "dtm")$document
                    speeches.out <- prepDocuments(docs, vocab, data.frame(speeches$party, speeches$campaigndays, speeches$campaigndaysend, speeches$summary, speeches$POTUS, speeches$SpeechID), lower.thresh=0)
                    print("Loaded prepared data.")
                }, error = function(cond) {
                    # returns: documents, vocab, meta, docs.removed
                    speeches.postproc <- textProcessor(documents = speeches$jointtokens,
                                            metadata = data.frame(speeches$party, speeches$campaigndays, speeches$campaigndaysend, speeches$summary, speeches$POTUS, speeches$SpeechID),
                                            lowercase = FALSE,
                                            removestopwords = FALSE,
                                            removenumbers = TRUE,
                                            removepunctuation = FALSE,
                                            stem = FALSE,
                                            wordLengths = c(3,Inf),
                                            sparselevel = 1,
                                            language = "en",
                                            verbose = TRUE,
                                            onlycharacter = FALSE,
                                            striphtml = FALSE,
                                            customstopwords = c("thank", "kamala", "harris", "kamala harris", "mike", 
                                                                "mike pence", "pence", "donald", "donald trump", 
                                                                "trump", "joe", "biden", "joe biden"), 
                                            v1 = FALSE)
                    speeches.out <- prepDocuments(speeches.postproc$documents, speeches.postproc$vocab, speeches.postproc$meta, lower.thresh=1)

                }
            )

            if (use_content_variable == 1) {
                if (use_time_variable == 1){
                    speeches.searchK <- searchK(documents = speeches.out$documents,
                                vocab = speeches.out$vocab,
                                K = topicnum,
                                proportion = 0.5, # default
                                heldout.seed = 1234,
                                M = 20, # number of words used to compute coherence and exclusivity
                                cores = 8,
                                prevalence = ~speeches.party + s(speeches.campaigndays),
                                content = ~speeches.party,
                                max.em.its = 100,
                                data = speeches.out$meta,
                                init.type = "Spectral",
                                verbose = TRUE
                                )
                } else {
                    speeches.searchK <- searchK(documents = speeches.out$documents,
                                vocab = speeches.out$vocab,
                                K = topicnum,
                                proportion = 0.5, # default
                                heldout.seed = 1234,
                                M = 20, # number of words used to compute coherence and exclusivity
                                cores = 8,
                                prevalence = ~speeches.party + s(speeches.campaigndaysend),
                                content = ~speeches.party,
                                max.em.its = 100,
                                data = speeches.out$meta,
                                init.type = "Spectral",
                                verbose = TRUE
                                )
                }
            } else {
                if (use_time_variable == 1){
                    speeches.searchK <- searchK(documents = speeches.out$documents,
                            vocab = speeches.out$vocab,
                            K = topicnum,
                            proportion = 0.5, # default
                            heldout.seed = 1234,
                            M = 20, # number of words used to compute coherence and exclusivity
                            cores = 8,
                            prevalence = ~speeches.party + s(speeches.campaigndays),
                            max.em.its = 100,
                            data = speeches.out$meta,
                            init.type = "Spectral",
                            verbose = TRUE
                            )
                } else {
                    speeches.searchK <- searchK(documents = speeches.out$documents,
                            vocab = speeches.out$vocab,
                            K = topicnum,
                            proportion = 0.5, # default
                            heldout.seed = 1234,
                            M = 20, # number of words used to compute coherence and exclusivity
                            cores = 8,
                            prevalence = ~speeches.party + s(speeches.campaigndaysend),
                            max.em.its = 100,
                            data = speeches.out$meta,
                            init.type = "Spectral",
                            verbose = TRUE
                            )
                }
            }
            # Use speeches.searchK$results$lbound in comparisons between models
            save(speeches.searchK, file=sprintf("%s/search_best_topicNum_model.rdata", DIR))
            for (k in topicnum){
                if (use_content_variable == 1){
                    DIR_out <- sprintf("%s/topics%d/party_prevalence_content/", DIR, k)
                    # print(DIR_out)
                    dir.create(file.path(DIR, sprintf("topics%d", k)), showWarnings = FALSE)
                    dir.create(file.path(sprintf("%s/topics%d/", DIR, k), "party_prevalence_content"), showWarnings = FALSE)
                } else {
                    DIR_out <- sprintf("%s/topics%d/party_prevalence/", DIR, k)
                    dir.create(file.path(DIR, sprintf("topics%d", k)), showWarnings = FALSE)
                    dir.create(file.path(sprintf("%s/topics%d/", DIR, k), "party_prevalence"), showWarnings = FALSE)
                }
                jpeg(sprintf("%s/model_search.jpeg", DIR_out))
                plot(speeches.searchK)
                dev.off()
                Sys.sleep(0.5)
                # different starting points for model estimation
                if (use_content_variable == 1) {
                    if (use_time_variable == 1){
                        speechesSelect <- selectModel(
                                        speeches.out$documents, 
                                        speeches.out$vocab, 
                                        K = k, 
                                        M = 20,
                                        prevalence = ~speeches.party + s(speeches.campaigndays),
                                        content = ~speeches.party,
                                        max.em.its = 200,
                                        data = speeches.out$meta,
                                        runs = 30,                                 
                                        seed = 8458159,
                                        init.type = "Spectral",
                                        verbose = TRUE,
                                        LDAbeta = LDAbeta)
                    } else {
                        speechesSelect <- selectModel(
                                        speeches.out$documents, 
                                        speeches.out$vocab, 
                                        K = k, 
                                        M = 20,
                                        prevalence = ~speeches.party + s(speeches.campaigndaysend),
                                        content = ~speeches.party,
                                        max.em.its = 200,
                                        data = speeches.out$meta,
                                        runs = 30,                                 
                                        seed = 8458159,
                                        init.type = "Spectral",
                                        verbose = TRUE,
                                        LDAbeta = LDAbeta)
                    }
                } else {
                    if (use_time_variable == 1){                        
                        speechesSelect <- selectModel(
                                        speeches.out$documents, 
                                        speeches.out$vocab, 
                                        K = k, 
                                        M = 20,
                                        prevalence = ~speeches.party + s(speeches.campaigndays),                            
                                        max.em.its = 200,
                                        data = speeches.out$meta,
                                        runs = 30,                             
                                        seed = 8458159,
                                        init.type = "Spectral",
                                        verbose = TRUE,
                                        LDAbeta = LDAbeta)
                    } else {                        
                        speechesSelect <- selectModel(
                                        speeches.out$documents, 
                                        speeches.out$vocab, 
                                        K = k, 
                                        M = 20,
                                        prevalence = ~speeches.party + s(speeches.campaigndaysend),                            
                                        max.em.its = 200,
                                        data = speeches.out$meta,
                                        runs = 30,                             
                                        seed = 8458159,
                                        init.type = "Spectral",
                                        verbose = TRUE,
                                        LDAbeta = LDAbeta)
                    }
                }
                
                save(speechesSelect, file=sprintf("%s/stm_selectmodel_%d_topics.rdata", DIR_out, k))
                # semantic coherence: it is maximized when the most probable words in a given topic frequently co-occur together.
                # exclusivity of words to topics, to avoid high coherence due to very common words in some topics (*)

                # plot FREX measure combining the two previous, per topic, to see variation in parameters
                jpeg(sprintf("%s/top_likelihood_models_evaluation.jpeg", DIR_out), width=680, height=680)
                plotModels(speechesSelect, pch = NULL, legend.position = "bottomright")
                dev.off()
                Sys.sleep(0.5)
                
                # all models in speechesSelect are high-likelihood
                # the user should check to make sure that sparsity is high enough (> 0.5), and then should select a model based on semantic coherence       
                if (use_content_variable == 1) {
                    speechesSelect$medianSparsity <- apply(data.frame(speechesSelect$sparsity), 2, median, na.rm=T)
                    indexmodels <- as.integer(which(speechesSelect$medianSparsity > 0.5))                   
                } else {
                    indexmodels <- seq(1, length(speechesSelect$runout), by = 1)
                }
                speechesSelect$medianSemCoh <- apply(data.frame(speechesSelect$semcoh), 2, median, na.rm=T)
                # pick best based on max median semantic coherence of sparse models
                best_model <- as.integer(which.max(speechesSelect$medianSemCoh[indexmodels]))                
                speeches.fit.partycovariate <- speechesSelect$runout[[best_model]]
                speechesSelect$bestmodel <- best_model
                
                print(speeches.fit.partycovariate)
                save(speechesSelect, file=sprintf("%s/stm_selectmodel_%d_topics.rdata", DIR_out, k))

                save(speeches.fit.partycovariate, file=sprintf("%s/stm_model_%d_topics.rdata", DIR_out, k))
                modelout <- make.dt(speeches.fit.partycovariate, speeches.out$meta)
                write.table(modelout, sprintf("%s/modelout_dataframe.csv", DIR_out), sep="\t", row.names=FALSE)
                Sys.sleep(0.5)
                k <- speeches.fit.partycovariate$settings$dim$K
                stars <- rep(0, k)
                stars2 <- rep(0, k)
                timecoefnum <- rep(0, k)
                if (use_time_variable == 1) {
                    dir.create(file.path(DIR_out, "estimateEffects"), showWarnings = FALSE)
                    speeches.out$meta$speeches.party <- as.factor(speeches.out$meta$speeches.party)
                    prep <- estimateEffect(~ speeches.party + s(speeches.campaigndays), speeches.fit.partycovariate, meta = speeches.out$meta, uncertainty = "Global")            
                    for (iii in seq(1, k, b=1)){                
                        sink(sprintf("%s/estimateEffects/estimateEffect_topic_%d_summary.txt", DIR_out, iii))
                        sumsum <- summary(prep, topics = iii)
                        timecovs = length(sumsum$tables[[1]])/4 - 2 # 1 intercept, 1 party, 10 time covariates, start p val from 1st time covariate
                        significance5 <- sumsum$tables[[1]][((timecovs+2)*3+2+1):((timecovs+2)*3+2+timecovs)]    
                        stars[iii] <- sum(significance5 < 0.05)
                        timecoefnum[iii] <- timecovs
                        print(sumsum)
                        sink()

                        jpeg(sprintf("%s/estimateEffects/topic_prevalence_smoothFunction_timeCov_topic_%d.jpeg", DIR_out, iii), width=680, height=680) 
                        plot(prep, "speeches.campaigndays", method = "continuous", topics = iii, model = speeches.fit.partycovariate, printlegend = FALSE, xlab = sprintf("Days from reference points - %s", timeframe))
                        dev.off()
                        Sys.sleep(0.5)

                        # content covariate - plot the interaction between time (day) and party. Topic i prevalence is plotted as linear
                        # function of time, holding the party at either Democrat or Republican
                        prep2 <- estimateEffect(c(iii) ~ speeches.party * speeches.campaigndays, speeches.fit.partycovariate, metadata = speeches.out$meta, uncertainty = "Global")
                        sink(sprintf("%s/estimateEffects/estimateEffect_topic_%d_DayParty_Interaction_summary.txt", DIR_out, iii))
                        sumsum2 <- summary(prep2)
                        stars2[iii] <- if (sumsum2$tables[[1]][16] < 0.05) 1 else 0
                        print(sumsum2)
                        sink()
                        jpeg(sprintf("%s/estimateEffects/content_covariate_DayParty_interaction_topic_%d_Democrats_Republicans.jpeg", DIR_out, iii), width=680, height=680)                
                        plot(prep2, covariate = "speeches.campaigndays", model = speeches.fit.partycovariate, method = "continuous", xlab = "Days from reference date", moderator = "speeches.party", moderator.value = "Democrats", linecol = "blue", ylim = c(-0.50, 0.50), printlegend = FALSE)                
                        plot(prep2, covariate = "speeches.campaigndays", model = speeches.fit.partycovariate, method = "continuous", xlab = "Days from reference date", moderator = "speeches.party", moderator.value = "Republicans", linecol = "red", add = TRUE, printlegend = FALSE)
                        legend(-0.5, -0.3, c("Democrat", "Republican"), lwd = 2, col = c("blue", "red"))
                        dev.off()
                        Sys.sleep(0.5)

                        jpeg(sprintf("%s/estimateEffects/content_covariate_Party_TopicDifference_topic_%d.jpeg", DIR_out, iii), width=680, height=680)                
                        plot(prep, covariate = "speeches.party", topics = c(iii), model = speeches.fit.partycovariate, method = "difference", cov.value1 = "Republicans", cov.value2 = "Democrats", xlab = "More Democrats ... More Republicans", main = "Effect of Republican vs. Democratic candidate", xlim = c(-0.1, 0.1))
                        dev.off()
                        Sys.sleep(0.5)
                    }
                } else {
                    dir.create(file.path(DIR_out, "estimateEffects"), showWarnings = FALSE)
                    speeches.out$meta$speeches.party <- as.factor(speeches.out$meta$speeches.party)
                    prep <- estimateEffect(~ speeches.party + s(speeches.campaigndaysend), speeches.fit.partycovariate, meta = speeches.out$meta, uncertainty = "Global")            
                    for (iii in seq(1, k, b=1)){                
                        sink(sprintf("%s/estimateEffects/estimateEffect_topic_%d_summary.txt", DIR_out, iii))
                        sumsum <- summary(prep, topics = iii)
                        timecovs = length(sumsum$tables[[1]])/4 - 2 # 1 intercept, 1 party, 10 time covariates, start p val from 1st time covariate
                        significance5 <- sumsum$tables[[1]][((timecovs+2)*3+2+1):((timecovs+2)*3+2+timecovs)]  
                        stars[iii] <- sum(significance5 < 0.05)
                        timecoefnum[iii] <- timecovs
                        print(sumsum)           
                        sink()

                        jpeg(sprintf("%s/estimateEffects/topic_prevalence_smoothFunction_timeCov_topic_%d.jpeg", DIR_out, iii), width=680, height=680) 
                        plot(prep, "speeches.campaigndaysend", method = "continuous", topics = iii, model = speeches.fit.partycovariate, printlegend = FALSE, xlab = sprintf("Days from reference points - %s", timeframe))
                        dev.off()
                        Sys.sleep(0.5)

                        # content covariate - plot the interaction between time (day) and party. Topic i prevalence is plotted as linear
                        # function of time, holding the party at either Democrat or Republican
                        prep2 <- estimateEffect(c(iii) ~ speeches.party * speeches.campaigndaysend, speeches.fit.partycovariate, metadata = speeches.out$meta, uncertainty = "Global")
                        sink(sprintf("%s/estimateEffects/estimateEffect_topic_%d_DayParty_Interaction_summary.txt", DIR_out, iii))
                        sumsum2 <- summary(prep2)
                        stars2[iii] <- if (sumsum2$tables[[1]][16] < 0.05) 1 else 0
                        print(sumsum2)
                        sink()
                        jpeg(sprintf("%s/estimateEffects/content_covariate_DayParty_interaction_topic_%d_Democrats_Republicans.jpeg", DIR_out, iii), width=680, height=680)                
                        plot(prep2, covariate = "speeches.campaigndaysend", model = speeches.fit.partycovariate, method = "continuous", xlab = "Days from reference date", moderator = "speeches.party", moderator.value = "Democrats", linecol = "blue", ylim = c(-0.50, 0.50), printlegend = FALSE)                
                        plot(prep2, covariate = "speeches.campaigndaysend", model = speeches.fit.partycovariate, method = "continuous", xlab = "Days from reference date", moderator = "speeches.party", moderator.value = "Republicans", linecol = "red", add = TRUE, printlegend = FALSE)
                        legend(-0.5, -0.3, c("Democrat", "Republican"), lwd = 2, col = c("blue", "red"))
                        dev.off()
                        Sys.sleep(0.5)

                        jpeg(sprintf("%s/estimateEffects/content_covariate_Party_TopicDifference_topic_%d.jpeg", DIR_out, iii), width=680, height=680)                
                        plot(prep, covariate = "speeches.party", topics = c(iii), model = speeches.fit.partycovariate, method = "difference", cov.value1 = "Republicans", cov.value2 = "Democrats", xlab = "More Democrats ... More Republicans", main = "Effect of Republican vs. Democratic candidate", xlim = c(-0.1, 0.1))
                        dev.off()
                        Sys.sleep(0.5)
                    }
                }                
                timeInTopicSignif <- stars
                timeInPartySignif <- stars2
                timecoef <- timecoefnum
                signifdf <- data.frame(timeInTopicSignif, timeInPartySignif, timecoef)
                write.table(signifdf, sprintf("%s/estimateEffects/timecovariate_significance.csv", DIR_out), sep=",", row.names=FALSE)
            
                # words associated with each topic
                speeches.labels_partycovariate <- labelTopics(speeches.fit.partycovariate)

                print("labelTopics")
                sink(sprintf("%s/labelTopics.txt", DIR_out))
                print(speeches.labels_partycovariate)
                sink()

                jpeg(sprintf("%s/indicative_words_per_topic.jpeg", DIR_out), width=680, height=680)
                par(omi = c(0,0,0,0), mgp = c(0,0,0), mar = c(0,0,0,0), family = "D")
                plot(speeches.fit.partycovariate, type = "labels")
                dev.off()
                Sys.sleep(0.5)

                # histogram of the expected distribution of topic proportions across the documents
                jpeg(sprintf("%s/distribution_topic_proportions_over_documents.jpeg", DIR_out), width=680, height=680)
                par(omi = c(0,0,0,0), mgp = c(0,0,0), mar = c(0,0,0,0), family = "D")
                plot(speeches.fit.partycovariate, type = "hist")
                dev.off()
                Sys.sleep(0.5)
                
                checktopics <- checkBeta(speeches.fit.partycovariate)
                if (checktopics$checked == TRUE){
                    save(checktopics, file=sprintf("%s/checkBeta_%d_topics_ok.rdata", DIR_out, k))
                }
                else {
                    save(checktopics, file=sprintf("%s/checkBeta_%d_topics_not_ok.rdata", DIR_out, k))
                }
                res_test <- checkResiduals(speeches.fit.partycovariate, speeches.out$documents)
                print(res_test)
                if (!is.na(res_test$pvalue) && res_test$pvalue < 0.05){
                    write.table(data.frame(res_test), sprintf("%s/checkResiduals_rejectnull.csv", DIR_out), sep=",", row.names=FALSE)
                } else if (is.na(res_test$pvalue) == TRUE) {
                    write.table(data.frame(res_test), sprintf("%s/checkResiduals_error.csv", DIR_out), sep=",", row.names=FALSE)
                } else {
                    write.table(data.frame(res_test), sprintf("%s/checkResiduals_ok.csv", DIR_out), sep=",", row.names=FALSE)
                } 
                Sys.sleep(0.5)

                if (LDAbeta == FALSE) {     
                    # the regularization of the SAGE model ensures that words load onto topics only when they have sufficient counts to overwhelm
                    # the prior. In general, this means that SAGE topics have fewer unique words that distinguish
                    # one topic from another, but those words are more likely to be meaningful.       
                    # default when a content covariate is used
                    sagemodel <- sageLabels(speeches.fit.partycovariate, n=30) 
                    write.table(data.frame(sagemodel$marginal), sprintf("%s/sage_marginal.csv", DIR_out), sep=",", row.names=FALSE)
                    write.table(data.frame(sagemodel$kappa), sprintf("%s/sage_topickappa.csv", DIR_out), sep=",", row.names=FALSE)
                    write.table(data.frame(sagemodel$kappa.m), sprintf("%s/sage_baselinekappa.csv", DIR_out), sep=",", row.names=FALSE)
                    write.table(data.frame(sagemodel$cov.betas), sprintf("%s/sage_covbetas.csv", DIR_out), sep=",", row.names=FALSE)
                    save(sagemodel, file=sprintf("%s/sageLabels_%d_topics.rdata", DIR_out, k))
                    Sys.sleep(0.5)
                }

                if (use_content_variable == 1){
                    dir.create(file.path(DIR_out, "topic_perspectives"), showWarnings = FALSE)
                    dir.create(file.path(DIR_out, "topic_perspectives_pairs"), showWarnings = FALSE)        
                }
                dir.create(file.path(DIR_out, "topic_quotes"), showWarnings = FALSE)
                dir.create(file.path(DIR_out, "wordclouds"), showWarnings = FALSE)
                for (i in seq(1, k, by = 1)){
                    if (use_content_variable == 1) {
                        # for content covariate influence - shows which words within a topic are more associated with one covariate value versus another
                        jpeg(sprintf("%s/topic_perspectives/topic_%d_wordsassociation.jpeg", DIR_out, i), width=680, height=680)
                        par(omi = c(0, 0, 0, 0), mgp = c(0, 0, 0), mar = c(0, 0, 0, 0), family = "D")
                        plot(speeches.fit.partycovariate, type="perspectives", topics=i)         
                        dev.off()
                        Sys.sleep(0.5)
                        if (i < k-1){
                            for (jj in seq((i+1), k, by=1)){                                      
                                jpeg(sprintf("%s/topic_perspectives_pairs/topics_%d_%d.jpeg", DIR_out, i, jj), width=680, height=680)
                                # par(omi = c(0, 0, 0, 0), mgp = c(0, 0, 0), mar = c(0, 0, 0, 0), family = "D")
                                plot(speeches.fit.partycovariate, type = "perspectives", topics = c(i, jj))
                                dev.off()
                                Sys.sleep(0.5)
                            }
                        }
                    }
                    # print the documents highly associated with each topic            
                    tryCatch({
                        thoughts <- findThoughts(speeches.fit.partycovariate, texts = as.character(speeches.out$meta$speeches.summary), n = 5, topics = i, thresh=0.6)$docs[[1]]            
                        jpeg(sprintf("%s/topic_quotes/topic_%d_thoughts.jpeg", DIR_out, i), width=680, height=680)
                        plotQuote(thoughts, width = 80, main = sprintf("Topic %d", i))
                        dev.off()
                        Sys.sleep(0.5)
                        },
                        error=function(cond){
                            dev.off()
                            thoughts <- findThoughts(speeches.fit.partycovariate, texts = as.character(speeches.out$meta$speeches.summary), n = 5, topics = i)$docs[[1]]            
                            jpeg(sprintf("%s/topic_quotes/topic_%d_thoughts_nothreshold.jpeg", DIR_out, i), width=680, height=680)
                            plotQuote(thoughts, width = 80, main = sprintf("Topic %d", i))
                            dev.off()
                        }
                    )

                    tryCatch({
                        # plots words within documents that have a topic proportion of higher than thresh
                        jpeg(sprintf("%s/wordclouds/topic_%d_doc.jpeg", DIR_out, i), width=680, height=680)
                        cloud(
                            speeches.fit.partycovariate,
                            topic = i,
                            type = "documents",
                            speeches.out$documents,
                            thresh = 0.6,
                            max.words = 100
                        )
                        dev.off()
                        Sys.sleep(0.5)
                        },
                        error=function(cond){
                            dev.off()
                            jpeg(sprintf("%s/wordclouds/topic_%d_doc_threshold_0.jpeg", DIR_out, i), width=680, height=680)
                            cloud(
                                speeches.fit.partycovariate,
                                topic = i,
                                type = "documents",
                                speeches.out$documents,
                                thresh = 0.0,
                                max.words = 100
                            )
                            dev.off()
                        }
                    )

                    # based on the probability of the word given the topic
                    jpeg(sprintf("%s/wordclouds/topic_%d.jpeg", DIR_out, i), width=680, height=680)
                    cloud(
                        speeches.fit.partycovariate,
                        topic = i,
                        type = "model",
                        max.words = 100
                        )
                    dev.off()
                    Sys.sleep(0.5)
                }
                # marginal distribution of words in corpus
                jpeg(sprintf("%s/wordclouds/marginal_words_corpus.jpeg", DIR_out), width=680, height=680)
                cloud(
                    speeches.fit.partycovariate,
                    topic = NULL,
                    max.words = 100
                    )
                dev.off()
                Sys.sleep(0.5)

                # expected proportion of the corpus that belongs to each topic
                jpeg(sprintf("%s/corpus_proportion_over_topics.jpeg", DIR_out), width = 680, height = 680)  
                # par(omi = c(0, 0, 0, 0), mgp = c(0, 0, 0), mar = c(0, 0, 2, 0), family = "D")
                plot(speeches.fit.partycovariate, type = "summary")
                dev.off()
                Sys.sleep(0.5)
                # correlations between topics - positive correlations between topics indicate that 
                # both topics are likely to be discussed within a document
                mod.out.corr <- topicCorr(speeches.fit.partycovariate, method = "huge", verbose = TRUE)
                save(mod.out.corr, file=sprintf("%s/stm_topicCorr_out.rdata", DIR_out))
                jpeg(sprintf("%s/corpus_topics_correlation.jpeg", DIR_out), width=680, height=680)    
                plot(mod.out.corr)
                dev.off()
                Sys.sleep(0.5)
                # approximate convergence, print variational bound
                jpeg(sprintf("%s/convergence_lbound.jpeg", DIR_out), width=680, height=680)    
                plot(speeches.fit.partycovariate$convergence$bound, type = "l", ylab = "Approximate Objective", main = "Convergence")
                dev.off()
                Sys.sleep(0.5)

                # correlations between topics - positive correlations between topics indicate that 
                # both topics are likely to be discussed within a document                                
                write.table(as.data.frame(as.matrix(mod.out.corr$posadj)), sprintf("%s/topicCorr_posAdj.csv", DIR_out), sep=",", row.names=FALSE)
                write.table(as.data.frame(as.matrix(mod.out.corr$poscor)), sprintf("%s/topicCorr_posCorr.csv", DIR_out), sep=",", row.names=FALSE)
                write.table(as.data.frame(as.matrix(mod.out.corr$cor)), sprintf("%s/topicCorr_Corr.csv", DIR_out), sep=",", row.names=FALSE)
                Sys.sleep(0.5) 
                
                stm_tidy <- tidy(speeches.fit.partycovariate)
                gpl <- stm_tidy  %>% 
                    dplyr::group_by(topic) %>%
                    dplyr::top_n(10, beta) %>% 
                    dplyr::ungroup() %>% 
                    dplyr::mutate(topic = paste0("Topic ", topic),
                        term = reorder_within(term, beta, topic))  %>% 
                    ggplot(aes(term, beta, fill = as.factor(topic))) +
                    geom_col(alpha = 0.8, show.legend = FALSE) +
                    facet_wrap(~ topic, scales = "free_y") +
                    coord_flip() +
                    scale_x_reordered() +
                    labs(x = NULL, y = expression(beta),
                        title = "Highest word probabilities for each topic",
                        subtitle = "Different words are associated with different topics")
                jpeg(sprintf("%s/word_probabilities_per_topic.jpeg", DIR_out), width=680, height=680) 
                plot(gpl)
                dev.off()
                Sys.sleep(0.5)
            }
        }
    }
}

