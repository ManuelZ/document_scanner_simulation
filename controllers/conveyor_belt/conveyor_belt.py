from controller import Supervisor

from math import radians as rad
import random

TIME_STEP = 10000


def initialize():
    robot = Supervisor()

    belt_motor = robot.getDevice("belt_motor")
    belt_motor.setPosition(float("inf"))
    belt_motor.setVelocity(0.15)

    return robot


def add_box(supervisor, model="1"):
    root_node = supervisor.getRoot()  # get root of the scene tree
    root_children_field = root_node.getField("children")

    box_models = ["1", "2"]

    # import at the end of the root children field
    root_children_field.importMFNodeFromString(
        -1,
        """
        CardboardBox1 {{
        name "CardboardBox1 {rot}"
        translation -0.16 8.2 0.94
        rotation 0 0 1 {rot}
        }}
        """.format(
            rot=rad(random.randint(0, 360)), model=random.choice(box_models)
        ),
    )


if __name__ == "__main__":
    supervisor = initialize()

    while supervisor.step(TIME_STEP) != -1:
        add_box(supervisor)

    supervisor.cleanup()
