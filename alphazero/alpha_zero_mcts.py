# coding: utf-8
import math
from typing import Tuple, Union

import numpy as np

from .bubble_board import BubbleBoard
from .node import Node
from .policy_value_net import PolicyValueNet


class AlphaZeroMCTS:
    """ 基于策略-价值网络的蒙特卡洛搜索树 """

    def __init__(self, policy_value_net: PolicyValueNet, c_puct: float, n_iters: int, is_self_play=False) -> None:
        """
        Parameters
        ----------
        policy_value_net: PolicyValueNet
            策略价值网络

        c_puct: float
            探索常数

        n_iters: int
            迭代次数

        is_self_play: bool
            是否处于自我博弈状态
        """
        self.c_puct = c_puct
        self.n_iters = n_iters
        self.is_self_play = is_self_play
        self.policy_value_net = policy_value_net
        self.root = Node(prior_prob=1, parent=None)

    def get_action(self, bubble_board: BubbleBoard) -> Union[Tuple[int, np.ndarray], int]:
        """ 根据当前局面返回下一步动作

        Parameters
        ----------
        bubble_board: BubbleBoard
            棋盘

        Returns
        -------
        action: int
            当前局面下的最佳动作

        pi: `np.ndarray` of shape `(board_len^2, )`
            执行动作空间中每个动作的概率，只在 `is_self_play=True` 模式下返回
        """
        for i in range(self.n_iters):
            # 拷贝棋盘
            board = bubble_board.copy()

            # 如果没有遇到叶节点，就一直向下搜索并更新棋盘
            node = self.root
            while not node.is_leaf_node():
                action, node = node.select()
                board.do_action(action)

            # 判断游戏是否结束或者深度受到限制，如果没结束就拓展叶节点
            if self.is_self_play:
                is_over, winner = board.is_game_over_with_limit(200)
            else:
                is_over, winner = board.is_game_over()

            p, value = self.policy_value_net.predict(board)
            player = board.current_player

            if not is_over:
                # TODO 是否需要一个随训练逐渐减少的噪音？
                node.expand(zip(board.available_actions, p))
            elif winner != 0:
                value = 1 if winner == player else -1
            else:
                value = 0

            # 反向传播
            node.backup(-value)

        t = 1 if self.is_self_play else 1e-3
        visits = np.array([i.N for i in self.root.children.values()])
        pi_ = self.__getPi(visits, t)

        # 根据 π 选出动作及其对应节点
        actions = list(self.root.children.keys())
        action = int(np.random.choice(actions, p=pi_))

        if self.is_self_play:
            # 创建维度为 board_len^2 的 π
            pi = np.zeros(bubble_board.board_len ** 2)
            pi[actions] = pi_
            # 更新根节点
            self.root = self.root.children[action]
            self.root.parent = None
            return action, pi
        else:
            self.reset_root()
            return action

    def __getPi(self, visits, T) -> np.ndarray:
        """ 根据节点的访问次数计算 π """
        # pi = visits**(1/T) / np.sum(visits**(1/T)) 会出现标量溢出问题，所以使用对数压缩
        x = 1 / T * np.log(visits + 1e-11)
        x = np.exp(x - x.max())
        pi = x / x.sum()
        return pi

    def reset_root(self):
        """ 重置根节点 """
        self.root = Node(prior_prob=1, c_puct=self.c_puct, parent=None)

    def set_self_play(self, is_self_play: bool):
        """ 设置蒙特卡洛树的自我博弈状态 """
        self.is_self_play = is_self_play
