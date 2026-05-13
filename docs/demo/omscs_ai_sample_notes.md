# OMSCS AI Sample Notes

Artificial Intelligence studies rational agents that perceive their environment and choose actions to maximize expected performance. A rational agent can be described by its performance measure, environment, actuators, and sensors.

Search algorithms solve problems by exploring state spaces. Breadth-first search expands the shallowest nodes first and is complete when the branching factor is finite. Depth-first search uses less memory but can get stuck in deep or infinite paths.

Heuristic search uses problem-specific estimates to guide exploration. A star search combines the path cost so far with an admissible heuristic estimate of remaining cost. When the heuristic never overestimates the true cost, A star can find optimal solutions under standard assumptions.

Adversarial search models competitive environments such as games. Minimax chooses moves by assuming the opponent also plays optimally. Alpha-beta pruning reduces the number of nodes evaluated without changing the final minimax decision.

Knowledge representation gives agents a way to store and reason about facts. Propositional logic represents true or false statements, while first-order logic can represent objects, relations, and quantified claims.

Planning focuses on choosing a sequence of actions that transforms an initial state into a goal state. A planning problem typically defines actions, preconditions, effects, and goals.

Key exam themes include rational agents, state-space search, heuristic quality, adversarial reasoning, logical representation, and planning operators.
