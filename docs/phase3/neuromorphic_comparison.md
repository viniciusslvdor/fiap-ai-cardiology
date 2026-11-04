# Logistic Regression vs. LIF spiking network on ECG time series

Notebook: [`notebooks/neuromorphic_lif_vs_logreg.ipynb`](../../notebooks/neuromorphic_lif_vs_logreg.ipynb) ·
Figures and metrics: [`results/neuromorphic/`](../../results/neuromorphic/)

## Data

The data comes from the PTB Diagnostic ECG database (Kaggle *ECG Heartbeat Categorization*). It has 14,552
heartbeats, each a series of 187 values at 125 Hz (about 1.5 s), labeled normal (4,046) or abnormal (10,506). We used
a stratified 80/20 split with seed 42, the same split as the ECG MLP notebook: 11,641 heartbeats for training and
2,911 for testing.

## Models

- **A, Logistic Regression.** The 187 standardized values are the inputs. Each instant is an independent feature.
- **B, LIF network.** 200 leaky integrate-and-fire neurons receive the signal one step at a time.
  - Input current: $I_i[t] = w^x_i x[t] + w^{\Delta}_i (x[t]-x[t-1]) + b_i$, with fixed random weights.
  - Membrane: $V \leftarrow V + (-V + I)/\tau$, with τ = 8 steps (64 ms).
  - When $V \ge 1$, the neuron spikes, resets and stays refractory for 2 steps.
  - The spike count of each neuron in 8 time windows (1,600 features) feeds a logistic regression. Only this readout is trained.
- **C, control.** The same random weights and windows as B, but with the ReLU of the current instead of spikes. It shows whether B's result comes from the spiking dynamics or from the larger number of features.

## Results

| Model | Accuracy | Balanced acc. | Recall abnormal | Recall normal | Precision abnormal | F1 | ROC-AUC |
|---|---|---|---|---|---|---|---|
| A, Logistic Regression | 0.786 | 0.785 | 0.787 | 0.782 | 0.904 | 0.842 | 0.871 |
| B, LIF (200 neurons) | 0.867 | 0.868 | 0.865 | 0.870 | 0.945 | 0.904 | 0.937 |
| C, control without spikes | 0.946 | 0.945 | 0.948 | 0.942 | 0.977 | 0.962 | 0.984 |
| ECG MLP (reference) | 0.962 | | | | | 0.973 | |

**Number of neurons**

| LIF neurons | 25 | 50 | 100 | 200 | 400 |
|---|---|---|---|---|---|
| Accuracy | 0.766 | 0.805 | 0.841 | 0.867 | 0.889 |
| Spikes per beat | 18 | 68 | 120 | 255 | 582 |

**Accuracy with Gaussian noise added to the test signals** (models trained on clean data)

| Noise σ | 0 | 0.02 | 0.05 | 0.10 | 0.20 |
|---|---|---|---|---|---|
| A, Logistic Regression | 0.786 | 0.764 | 0.690 | 0.644 | 0.603 |
| B, LIF | 0.867 | 0.849 | 0.779 | 0.693 | 0.706 |
| C, control | 0.946 | 0.794 | 0.687 | 0.557 | 0.411 |

**Cost per beat**

| Model | Dense operations | Spikes | Inference on CPU |
|---|---|---|---|
| A | 187 | — | ~0.001 ms |
| B | ~114,000 | ~255 (0.68% of neuron-steps) | ~0.44 ms |

## Analysis

**LIF vs. logistic regression.** The LIF network is better on every metric:

- accuracy: 0.867 vs 0.786;
- recall of abnormal beats: 0.865 vs 0.787;
- ROC-AUC: 0.937 vs 0.871.

Its accuracy also grows with the number of neurons, from 0.766 with 25 to 0.889 with 400. The logistic regression
treats each instant separately and cannot represent the shape of the waves. The LIF neurons combine the signal and
its slope over time, through the leak and the threshold. In `lif_dynamics.png` the activity concentrates on the
sharp parts of the beat.

**Control model.** On clean data the control reaches 0.946, better than B and close to the MLP. Most of the gain
over A therefore comes from the random nonlinear features. Converting them into spike counts discards information
below the threshold.

**Noise.** With noise the ranking changes. At σ = 0.02 the control drops to 0.794 while B stays at 0.849. At
σ = 0.2 the results are:

- control: 0.411, below the rate of always answering "abnormal" (0.722);
- LIF: 0.706;
- logistic regression: 0.603.

B is the most accurate model at every noise level tested. Two factors explain this:

- the membrane integrates the input over 64 ms, acting as a low-pass filter, and the threshold ignores small variations;
- the control's features depend directly on the slope of the signal, which amplifies noise.

For a wearable, where movement and skin contact add noise, this behavior is relevant.

**Efficiency.** On a CPU the LIF network is about 600 times slower than the logistic regression, because every
neuron is simulated at every step. Neuromorphic processors such as Intel Loihi or BrainChip Akida are event-driven:
their cost depends mainly on the number of spikes, here about 255 per beat with less than 1% of neurons active per
step. This is an estimate, as no neuromorphic hardware was used.

## Advantages and limitations

| | Logistic Regression | LIF network |
|---|---|---|
| Advantages | fast training (0.2 s), very low cost, interpretable weights | uses temporal information, better accuracy, more robust to noise, sparse activity |
| Limitations | ignores order and shape, lowest accuracy | expensive to simulate on a CPU, hyperparameters chosen by hand, loses information below the threshold |

General limitations of the experiment:

- The spiking layer is not trained. Training it with surrogate gradients (for example with snnTorch) could improve B.
- All models were trained only on clean data. Training with noise could change the ranking.
- There is a single seed and a single split.
- Beats are split randomly and not by patient (patient IDs are not available), so results are optimistic.
- The abnormal class mixes several diseases.

The FitzHugh–Nagumo (FHN) model reproduces the shape of an action potential better, but it is more expensive to
simulate. LIF is the model used by most neuromorphic hardware.

## Conclusion

The LIF network outperforms the logistic regression by about 8 points of accuracy and is the most robust model under
noise. On clean signals, the non-spiking control is even better, and neither model reaches the MLP. For CardioIA the
interest of the spiking approach is robustness and the potential for low-power continuous monitoring, not peak accuracy.
