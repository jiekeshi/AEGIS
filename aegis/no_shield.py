import json
import logging
import argparse

import numpy as np
from tqdm import tqdm
from DDPG import DDPG

import time
from envs import ENV_CLASSES
import numpy as np


logging.getLogger().setLevel(logging.INFO)


def refine(env, K, ce, test_episodes):
    epsilon = 1e-4
    learning_rate = 1e-3
    s = env.reset(np.array(ce).reshape([-1, 1]))

    for _ in range(test_episodes):
        a = K.dot(s)

        perturbation = np.zeros_like(K)
        for i in range(K.shape[0]):
            for j in range(K.shape[1]):
                perturbation[i, j] = epsilon

        K_plus = K + perturbation
        K_minus = K - perturbation

        a_plus = K_plus.dot(s)
        a_minus = K_minus.dot(s)

        s, r, terminal = env.step(a.reshape(actor.a_dim, 1))
        gradients = (env.reward(s, a_plus) - env.reward(s, a_minus)) / (2 * epsilon)
        K -= learning_rate * gradients
    return K


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Running Options")
    parser.add_argument(
        "--env", default="cartpole", type=str, help="The selected environment."
    )
    parser.add_argument("--do_eval", action="store_true", help="Test RL controller")
    parser.add_argument("--test_episodes", default=5000, help="test_episodes", type=int)
    parser.add_argument(
        "--do_retrain", action="store_true", help="retrain RL controller"
    )
    args = parser.parse_args()

    env = ENV_CLASSES[args.env]()
    with open("configs.json") as f:
        configs = json.load(f)

    DDPG_args = configs[args.env]
    DDPG_args["enable_retrain"] = args.do_retrain
    DDPG_args["enable_eval"] = args.do_eval
    DDPG_args["enable_fuzzing"] = False
    DDPG_args["enable_falsification"] = False

    DDPG_args["test_episodes"] = args.test_episodes
    actor = DDPG(env, DDPG_args)

    def run():
        total_rewards = 0
        volations = 0
        all_time = time.time()
        for i in tqdm(range(1)):
            s = env.reset()
            for i in range(args.test_episodes):
                a = actor.predict(s.reshape([1, actor.s_dim]))
                s, r, terminal = env.step(a.reshape(actor.a_dim, 1))
                total_rewards += r
                if terminal and i < args.test_episodes - 1:
                    volations += 1
                    # break
            all_time = time.time() - all_time

        return volations

    volations = run()
    logging.info(f"Violations: {volations}")
