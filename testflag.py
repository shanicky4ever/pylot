from absl import app, flags
import pylot.flags
FLAGS = flags.FLAGS


def main(argv):
    print(type(FLAGS))


if __name__ == '__main__':
    # app.run(main)
    app.run(main)
