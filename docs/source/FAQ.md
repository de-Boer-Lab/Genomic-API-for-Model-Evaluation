# FAQ

## Why can't you request specific assays from Predictors?

While modeling biophysical or assay specific biases has generally increased performance and interpretability of models we chose to make GAME assay agnostic for a variety of reasons. If we had not focused on predicting the biological phenomena, each Predictor would be required to both remove the bias from their training data and to inject the bias of their prediction task. For example, an ATAC-seq model would have to remove ATAC-seq bias and add DNaseI-seq bias for performing well on the DNaseI task. Using this approach, every model would have to know about every other experimental assay’s biases so that they could be added, including for assays that do not currently exist.

## How did an LLM Matcher come to be?

Current benchmarking studies for ML models manually align tasks between models and benchmarks, which is a tedious and subjective procedure and typically does not provide an adequate explanation for how task mappings were chosen. Maintaining this standard would require each Predictor builder to align their tasks to those of Evaluators and they would have to update the Predictor every time a new Evaluator with a new task was added. 

Our initial design for Matcher automated this procedure using cell type/cell line ontologies and a graph search algorithm. However, this required that each Predictor and Evaluator map its tasks into the ontology, which was a substantial challenge in itself, in particular for cases where many cell types/tissues had to be mapped. Further, the ontology was far from complete, leading to matches between cell types that our manual inspection revealed were far from optimal. This led us to test a LLM version of Matcher, which solved all the issues with the ontology-based matcher: the task annotations could be used directly and so never need updating, semantic issues/typos were easily resolved, and the matches appeared to be far better than the ontology-based approach. We then optimized the implementation and prompt engineering approaches to yield the current version of Matcher.

## LLM's aren't deterministic, could this be a problem?

It is true that Matcher's output depend on the exact inputs, which, if different, could yield different results. For example, if Predictor1 requests a match for B from A, C, and Z, while Predictor2 requests a match for B from A, C, and W, the Matcher could theoretically return the best match as A for Predictor1 and C for Predictor2. We have, however, made the Matcher deterministic by setting the “temperature” term to 0 so that the same input is much more likely produce the same output. We have also run multiple simulations using our LLM Matcher to show that when the input requests are fixed it produces identical responses, further providing confidence in its abilities.

## Can I fine tune modules using GAME?

No, only static models with fixed parameters/models weights can be used in the GAME framework. That being said foundational models that had already been fine-tuned to predict genome regulation from DNA sequence are fully compatible with GAME.

## Can I host a Predictor with proprietary model weights?

Yes, this is exactly why GAME is built around REST APIs. If you want to contribute a model with private weights, you can simply host your own Predictor server that others can connect to it.  

## Can I host an Evaluator with private data?

Yes, if you have private data that you don't want to share with others, you can add an encryption layer on top of your client. More on this coming soon!

## Why did you choose to use REST APIs?

1. The use of standardized HTTP error codes in conjunction with our descriptive error message to flag the Evaluators of any issues.
2. Inbuilt content headers in REST requests and responses provides standardization of formats and flexibility of message types.
3. Cross compatibility across different tools/programming that can be used to implement modules. While most of our modules use Flask to implement REST API, the Matcher module was implemented using FastAPI, serving as an example.
4. The use of a standardized and familiar API framework magnifies our goal to future proof this API and increases uptake by the community.
5. Additional infrastructure already exists for applications that are built using REST APIs, such as tools that allow multiple requests to be handled and approaches to ensure privacy of connections (TLS Encryption layers, Gunicorn). Since these can be used on top of an API built using REST, they would not require any changes to the framework.

## It sounds like a lot of work to make a module, why should I bother?

While the initial time commitment may seem daunting, we provide a diverse set of GAME Predictors and Evaluators that contributors can use as starting points. Once you build a container, you can seamlessly interact with all other modules in the framework.

## How can I integrate more complex models (ex. models that require inputs other than sequence) into GAME?

Predictor builders have complete flexibility to integrate any non-user provided information into their predictions, as long as it remains fixed after training. For instance, some models now use additional cell type/state embeddings as inputs. Predictors for such a use case would have to annotate the embedding with cell types and states, which could then be used to query the Matcher. The matcher can support arbitrarily specific cell annotations so even quite specific cell states could be captured (e.g. “Adult atrial cardiomyocyte in S phase adjacent to an endothelial cell responding to IFN”). The closest embedding to the requested cell type/state can be related back to the Predictor’s embedding to produce the final prediction.

## Is there anyway to flag potential train-test leakage between Evaluator and Predictor modules?

Train-test leakage is a prevalent and difficult problem in the field. Currently, there is no efficient way to check for sequence leakage or homology from the model’s training data to data that is being predicted on. Looking to the future, having more Evaluators that use synthetic data would be invaluable because leakage would be more obvious there (e.g. the model would have to have been trained on the same synthetic sequences). For this reason, we prioritized benchmarks that are based on synthetic sequences (or synthetic modifications to natural sequences), including Evaluators for a designed MPRA experiment, CRISPRi synthetically repressing endogenous enhancers, and a dataset that used Prime editing to introduce synthetic variants into the genome, reading out their expression.

## Why Apptainer and not Docker?

Apptainer provides users with increased flexibility (no root access requited) on HPC platforms which are crucial for making predictions using large models across thousands of sequences. Pre-built docker containers can still be used with GAME's apptainer implementation. For example, the ChromBPNet container builds a GAME container starting from a pre-built Docker image.

## Where can I report bugs?

Bugs can be reported on the Github Issues page for GAME or for specific modules on the GAME Modules page.
