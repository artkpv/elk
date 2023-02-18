import csv

import torch

from elk.training.preprocessing import load_hidden_states, normalize
from ..files import elk_cache_dir


def evaluate(args):
    """
    Note: eval is a reserved keyword in python, therefore we use evaluate instead
    """
    for hidden_state_dir in args.hidden_states:
        hiddens, labels = load_hidden_states(
            path=elk_cache_dir() / hidden_state_dir / "validation_hiddens.pt"
        )
        assert len(set(labels)) > 1

        _, hiddens = normalize(hiddens, hiddens, args.normalization)

        reporters = torch.load(elk_cache_dir() / args.reporters / "reporters.pt")
        L = hiddens.shape[1]

        statistics = []
        for reporter in reporters:
            reporter.eval()

            layers = list(hiddens.unbind(1))
            layers.reverse()

            with torch.no_grad():
                for hidden_state in layers:
                    x0, x1 = hidden_state.to(args.device).float().chunk(2, dim=-1)

                    result = reporter.score(
                        (x0, x1),
                        labels.to(args.device),
                    )
                    stats = [*result]
                    stats += [args.normalization, args.reporters, hidden_state_dir]
                    statistics.append(stats)

        cols = [
            "layer",
            "acc",
            "cal_acc",
            "auroc",
            "normalization",
            "reporters",
            "hidden_states",
        ]
        args.eval_dir.mkdir(parents=True, exist_ok=True)
        with open(args.eval_dir / f"{hidden_state_dir}_eval.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(cols)

            for i, stats in enumerate(statistics):
                writer.writerow([L - i] + [s for s in stats])

        print("Evaluation done.")