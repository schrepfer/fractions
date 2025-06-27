#!/usr/bin/env python3

"""Fractions program."""

import argparse
import enum
import fractions
import logging
import operator
import os
import random
import re
import sys

from typing import Any, Callable


BinaryOp = Callable[[Any, Any], Any]


class Operator(enum.Enum):
  """Operator Enum."""

  ADD = ('+', operator.add)
  SUB = ('-', operator.sub)

  def __new__(cls, *args):
    value = len(cls.__members__) + 1
    obj = object.__new__(cls)
    obj._value_ = value
    return obj

  @classmethod
  def argtype(cls, s: str) -> enum.Enum:
    try:
      return cls[s]
    except KeyError as e:
      raise argparse.ArgumentTypeError(
          f'{s!r} is not a valid {cls.__name__}') from e

  def __init__(self, display: str, op: BinaryOp):
    self._display = display
    self._op = op

  @property
  def display(self) -> str:
    return self._display

  @property
  def op(self) -> BinaryOp:
    return self._op

  def __repr__(self) -> str:
    return self.name

  def __str__(self) -> str:
    return self.display


def define_flags() -> argparse.Namespace:
  """Define the flags."""
  parser = argparse.ArgumentParser(description=__doc__)
  # See: http://docs.python.org/3/library/argparse.html
  parser.add_argument(
      '-v', '--verbosity',
      action='store',
      default=20,
      type=int,
      help='the logging verbosity',
      metavar='LEVEL',
  )
  parser.add_argument(
      '-d', '--denominator',
      action='store',
      default=16,
      choices=[1<<n for n in range(1, 8)],
      type=int,
      help='the denominator to randomize between',
      metavar='DENOMINATOR',
  )
  parser.add_argument(
      '-o', '--operators',
      action='store',
      default=[Operator.ADD],
      choices=Operator,
      type=Operator.argtype,
      nargs='+',
      help=('the operator(s) to use; choices: '
            + ', '.join(o.name for o in Operator)),
      metavar='TYPE',
  )
  parser.add_argument(
      '-x', '--canonical',
      action='store_true',
      help='require the canonical answer, i.e. 1-3/8',
  )
  parser.add_argument(
      '-~', '-e', '--estimate',
      action='store_true',
      help='show the estimated value too, i.e. 1.375',
  )
  parser.add_argument(
      '-V', '--version',
      action='version',
      version='fractions version 0.1',
  )

  args = parser.parse_args()
  check_flags(parser, args)
  return args


def check_flags(unused_parser, unused_args) -> None:
  # See: http://docs.python.org/3/library/argparse.html#exiting-methods
  return


_WHOLE_FORMAT = re.compile(r'(?P<whole>\d+)-(?P<num>\d+)/(?P<denom>\d+)')


class Fraction(fractions.Fraction):

  @property
  def estimate(self) -> float:
    return float(self.numerator) / self.denominator

  def __str__(self) -> str:
    if self.numerator >= self.denominator:
      whole = int(self.numerator / self.denominator)
      numerator = self.numerator % self.denominator
      if numerator == 0:
        return '{0:d}'.format(whole)
      return '{0:d}-{1}'.format(whole, Fraction(numerator, self.denominator))
    return super().__str__()


def get_random_fraction(denominator: int) -> Fraction:
  return Fraction(random.randint(1, denominator - 1), denominator)


_ENCOURAGEMENT: list[str] = [
    'You’re on the right track now!',
    'You’ve got it made.',
    'That’s right!',
    'That’s good.',
    'I’m very proud of you.',
    'You’re really working hard today.',
    'You are very good at that.',
    'That’s coming along nicely.',
    'Good work!',
    'I’m happy to see you working like that.',
    'That’s much, much better!',
    'Exactly right.',
    'I’m proud of the way you worked today.',
    'You’re doing that much better today.',
    'You’ve just about got it.',
    'That’s the best you’ve ever done.',
    'You’re doing a good job.',
    'That’s it!',
    'Now you’ve figured it out.',
    'That’s quite an improvement.',
    'Great!',
    'I knew you could do it.',
    'Congratulations!',
    'Not bad.',
    'Keep working on it.',
    'You’re improving.',
    'Now you have it!',
    'You are learning fast.',
    'Good for you!',
    'Couldn’t have done it better myself.',
    'Aren’t you proud of yourself?',
    'One more time and you’ll have it.',
    'You really make my job fun.',
    'That’s the right way to do it.',
    'You’re getting better every day.',
    'You did it that time!',
    'That’s not half bad.',
    'Nice going.',
    'You haven’t missed a thing!',
    'Wow!',
    'That’s the way!',
    'Keep up the good work.',
    'Terrific!',
    'Nothing can stop you now.',
    'That’s the way to do it.',
    'Sensational!',
    'You’ve got your brain in gear today.',
    'That’s better.',
    'That was first class work.',
    'Excellent!',
    'That’s the best ever.',
    'You’ve just about mastered it.',
    'Perfect!',
    'That’s better than ever.',
    'Much better!',
    'Wonderful!',
    'You must have been practicing.',
    'You did that very well.',
    'Fine!',
    'Nice going.',
    'You’re really going to town.',
    'Outstanding!',
    'Fantastic!',
    'Tremendous!',
    'That’s how to handle that.',
    'Now that’s what I call a fine job.',
    'That’s great.',
    'Right on!',
    'You’re really improving.',
    'You’re doing beautifully!',
    'Superb!',
    'Good remembering.',
    'You’ve got that down pat.',
    'You certainly did well today.',
    'Keep it up!',
    'Congratulations. You got it right!',
    'You did a lot of work today.',
    'Well look at you go.',
    'That’s it.',
    'I like knowing you.',
    'Marvelous!',
    'I like that.',
    'Way to go!',
    'Now you have the hang of it.',
    'You’re doing fine!',
    'Good thinking.',
    'You are really learning a lot.',
    'Good going.',
    'I’ve never seen anyone do it better.',
    'Keep on trying.',
    'You outdid yourself today!',
    'Good for you!',
    'I think you’ve got it now.',
    'That’s a good (boy/girl).',
    'Good job, (person’s name).',
    'You figured that out fast.',
    'You remembered!',
    'That’s really nice.',
    'That kind of work makes me happy.',
]


class Guess(object):
  """A Guess."""

  left: Fraction
  right: Fraction
  want: Fraction
  op: Operator
  n: int

  def __init__(self):
    self.reset(Fraction(0), Fraction(0), Operator.ADD)

  def reset(self, left: Fraction, right: Fraction, op: Operator):
    want = Fraction(op.op(left, right))
    if want >= 0:
      self.left, self.right = left, right
      self.want = want
    else:
      self.left, self.right = right, left
      self.want = -want
    self.op = op
    self.n = 0

  def prompt(self) -> str:
    self.n += 1
    return input(f'What is {self.left} {self.op} {self.right}? ').strip()


def main(args: argparse.Namespace) -> int:
  repeat: bool = False
  guess: Guess = Guess()
  interrupts: int = 0
  correct: int = 0
  incorrect: int = 0
  skipped: int = 0
  print('Answers in the format of: {whole}-{numerator}/{denominator}')
  print(' (simplified required)'
        if args.canonical else
        ' (1-1/4, 1.25, 5/4, 1-2/8 OK)')
  print('[Press ^C to move to the next question]')
  print('[Press ^D to quit]')
  print('')
  first = True
  while True:
    try:
      if not repeat or first:
        guess.reset(
            get_random_fraction(args.denominator),
            get_random_fraction(args.denominator),
            random.choice(args.operators))
      first = False
      raw = guess.prompt()
      interrupts = 0
      m = _WHOLE_FORMAT.match(raw)
      got: Fraction
      if m:
        whole = int(m.group('whole'))
        num = int(m.group('num'))
        denom = int(m.group('denom'))
        got = Fraction((whole*denom)+num, denom)
      else:
        got = Fraction(raw)
      if ((args.canonical and raw == f'{guess.want}')      # String
          or (not args.canonical and got == guess.want)):  # Value
        print('✔️  '
              + random.choice(_ENCOURAGEMENT)
              + (f' ({guess.want})' if not args.canonical else '')
              + (f' [{guess.want.estimate}]' if args.estimate else ''))
        correct += 1
        repeat = False
      else:
        print('❌ Try again! '
              + ('Simplify your answer. '
                 if args.canonical and got == guess.want else '')
              + '^C to move on.')
        incorrect += 1
        repeat = True
      print('')
    except ValueError:
      repeat = True
      continue
    except KeyboardInterrupt:
      print('')
      print(f'Wanted {guess.want}!\n')
      interrupts += 1
      skipped += 1
      repeat = False
      if interrupts > 2:
        print(f'[Multiple interrupts ({interrupts}) in a row. Quitting.]')
        break
    except EOFError:
      print('^D')
      print('')
      break
  correct_percent: float = 0
  if correct + incorrect > 0:
    correct_percent = 100.0 * correct / (correct + incorrect)
  print(f'[Correct: {correct} ({correct_percent:0.2f}%),'
        f' Incorrect: {incorrect},'
        f' Skipped: {skipped}]')
  return os.EX_OK


if __name__ == '__main__':
  a = define_flags()
  logging.basicConfig(
      level=a.verbosity,
      datefmt='%Y/%m/%d %H:%M:%S',
      format='[%(asctime)s] %(levelname)s: %(message)s')
  sys.exit(main(a))
