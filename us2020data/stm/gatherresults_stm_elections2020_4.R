################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

topicnums <- c(10, 15, 20, 25)
time <- 0
dictionary <- "POTUS2020"
DIR <- sprintf("%s/us2020data/stm/postprocessed4stm/%s/stm/", getwd(), dictionary)
all_subdirectories <- list.dirs(DIR, full.names = FALSE, recursive = FALSE)
times <- c()
ks <- c()
bounds <- c()
semcoh <- c()
sparsity <- c()
heldouts <- c()
for (subdir in all_subdirectories){
    print(subdir)
    if (time == 1) {
        dirdata <- sprintf("%s%s/LDAbeta_false/time_covariate/", DIR, subdir)
    } else {
        dirdata <- sprintf("%s%s/LDAbeta_false/", DIR, subdir)
    }
    load(sprintf("%s/search_best_topicNum_model.rdata", dirdata))
    foundK <- FALSE
    while (foundK == FALSE){
        maxind <- as.integer(which.max(speeches.searchK$results$lbound))
        besttopic <- topicnums[maxind]
        if (sum(is.na(speeches.searchK$results$lbound)) == 3) {
            print(sprintf("%s - choosing based on max ELBO", subdir))
            load(sprintf("%s/search_best_topicNum_model.rdata", dirdata))
            maxind <- as.integer(which.max(speeches.searchK$results$lbound))
            besttopic <- topicnums[maxind]
            break
        }
        if ( !(file.exists(sprintf("%stopics%d/party_prevalence_content/checkBeta_%d_topics_ok.rdata", dirdata, besttopic, besttopic)) & file.exists(sprintf("%stopics%d/party_prevalence_content/checkResiduals_ok.csv.rdata", dirdata, besttopic, besttopic))) ){
                speeches.searchK$results$lbound[[maxind]] <- NA
                foundK <- FALSE
                
        } else {
            foundK <- TRUE
        }
    }
    load(sprintf("%s/topics%d/party_prevalence_content/stm_selectmodel_%d_topics.rdata", dirdata, besttopic, besttopic))
    times <- c(times, subdir)
    ks <- c(ks, besttopic)
    bounds <- c(bounds, speeches.searchK$results$lbound[[maxind]])
    heldouts <- c(heldouts, speeches.searchK$results$heldout[[maxind]])
    semcoh <- c(semcoh, speechesSelect$medianSemCoh[[speechesSelect$bestmodel]])
    sparsity <- c(sparsity, speechesSelect$medianSparsity[[speechesSelect$bestmodel]])
}
outdf <- data.frame(times, ks, bounds, heldouts, semcoh, sparsity)
if (time == 1){
    write.table(outdf, sprintf("%s/selected_models_with_time_covariate.csv", DIR), sep=",", row.names=FALSE)
} else {
    write.table(outdf, sprintf("%s/selected_models.csv", DIR), sep=",", row.names=FALSE)
}
