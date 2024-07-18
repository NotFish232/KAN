from pathlib import Path

import torch as T
from torch.utils.data import Dataset, TensorDataset

from utils import gaussian
from utils.data_management import ExperimentDataType
from utils.experiment import run_experiment

EXPERIMENT_NAME = Path(__file__).stem

NUM_PEAKS = 5
NUM_POINTS = 1_000
GAUSSIAN_STD = 0.2
LINEAR_SLOPE = 0.2

KAN_ARCHITECTURE = [1, 1]
KAN_GRID_SIZE = 100
MLP_ARCHICTURE = [1, 16, 16, 1]

NUM_EPOCHS = 100


def create_dataset(device: T.device) -> tuple[T.Tensor, T.Tensor]:
    X = T.linspace(0, NUM_PEAKS, NUM_POINTS, device=device).unsqueeze(1)
    Y = T.linspace(0, LINEAR_SLOPE * NUM_PEAKS, NUM_POINTS, device=device).unsqueeze(1)
    for i in range(NUM_PEAKS):
        Y += gaussian(X, i + 0.5, GAUSSIAN_STD)

    return X, Y


def main() -> None:
    device = T.device("cuda" if T.cuda.is_available() else "cpu")

    X, Y = create_dataset(device)
    X_partitioned = list(T.chunk(X, NUM_PEAKS))
    Y_partitioned = list(T.chunk(Y, NUM_PEAKS))

    function_dataset = TensorDataset(X, Y)
    partitioned_datasets: list[Dataset] = []
    for X_batch, Y_batch in zip(X_partitioned, Y_partitioned):
        partitioned_datasets.append(TensorDataset(X_batch, Y_batch))

    run_experiment(
        EXPERIMENT_NAME,
        KAN_ARCHITECTURE,
        MLP_ARCHICTURE,
        partitioned_datasets,
        {"eval": function_dataset},
        {"function": X},
        {"function": Y, "task": Y_partitioned},
        ExperimentDataType.function_1d,
        kan_kwargs={
            "grid": KAN_GRID_SIZE,
            "grid_range": [0, NUM_PEAKS],
            "bias_trainable": False,
            "sp_trainable": False,
            "sb_trainable": False,
        },
        training_kwargs={"epochs": NUM_EPOCHS}
    )


if __name__ == "__main__":
    main()