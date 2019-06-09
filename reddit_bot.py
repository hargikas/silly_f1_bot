import datetime
import io
import re
from pathlib import Path

import praw
from praw.models import MoreComments

import next_race


def schedule_reply(comment, msg):
    try:
        schedule_reply.append((comment, msg))
    except AttributeError:
        schedule_reply.pending = [(comment, msg)]

    try:
        while schedule_reply.pending:
            cur_comment, cur_msg = schedule_reply.pending[0]
            cur_comment.refresh()
            if cur_comment.body and cur_comment.author:
                cur_comment.upvote()
                req_dt = datetime.datetime.utcfromtimestamp(
                    cur_comment.created_utc)
                res_dt = datetime.datetime.utcnow()
                diff_td = res_dt - req_dt
                cur_msg += '*Total time to respond: %d seconds.*' % (
                    diff_td.total_seconds())
                cur_comment.reply(cur_msg)

            del schedule_reply.pending[0]
    except praw.exceptions.APIException as exc:
        print('APIException:', exc.message)


def inspect_comments(subs):
    print("Inspecting comments of the selected subs")
    total = 0
    replied = 0
    bot_username = 'f1_predictor'
    regex = re.compile(bot_username, re.I)
    try:
        for comment in subs.stream.comments(skip_existing=True):
            if isinstance(comment, MoreComments):
                continue
            total += 1

            match = regex.search(comment.body)
            if match:
                print("I was called by /u/%s in /r/%s" %
                      (comment.author, comment.subreddit.display_name))
                replied += 1
                msg = 'Thank you /u/%s for summoning me!\n\n' % (
                    comment.author)

                ranking = False
                pairwise = False
                qualifying = False
                race = False

                for word in str(comment.body).split():
                    token = word.strip().lower()
                    if token in ['ranking', 'rank', 'order', 'position', 'positions', 'prediction']:
                        ranking = True
                    if token in ['pairs', 'pairwise', 'pair', 'probabilities', 'probability', 'prediction']:
                        pairwise = True
                    if token in ['qualifying', 'qualy', 'qual', 'GP']:
                        qualifying = True
                    if token in ['race', 'GP']:
                        race = True

                if (ranking or pairwise or qualifying or race):
                    # If none is specified we return both
                    if (not qualifying) and (not race):
                        qualifying = True
                        race = True

                    # If none is specified we return both
                    if (not ranking) and (not pairwise):
                        ranking = True
                        pairwise = True

                    prediction_data = next_race.get_prediction()
                    if prediction_data:
                        msg += "Prediction data for race: %s\n\n" % (
                            prediction_data['race_name'])
                        if qualifying:
                            part = prediction_data['qualifying']
                            if ranking:
                                msg += 'Qualification Ranking:\n\n'
                                msg += part['ranking_string'] + '\n\n'
                            if pairwise:
                                msg += 'Qualification Pairwise Probabilities:\n\n'
                                msg += part['probabilities_table_1'] + '\n\n'
                                msg += part['probabilities_table_2'] + '\n\n'
                        if race:
                            part = prediction_data['race']
                            if ranking:
                                msg += 'Race Ranking:\n\n'
                                msg += part['ranking_string'] + '\n\n'
                            if pairwise:
                                msg += 'Race Pairwise Probabilities:\n\n'
                                msg += part['probabilities_table_1'] + '\n\n'
                                msg += part['probabilities_table_2'] + '\n\n'
                    else:
                        msg += "Unfortunately I don't have any prediction for future events (qualifications, races)\n\n"
                else:
                    msg += "Sorry! I am naive and stupid and I couldn't understand your message...\n\n"

                msg += '*I am a bot, and this action was performed automatically.*\n'

                schedule_reply(comment, msg)

    except BaseException:
        print("Parsed %d comments and %d of them where replied" %
              (total, replied))
        raise


def load_subrredits(filename):
    subs = None
    with io.open(filename, 'r', encoding='utf-8') as f_obj:
        lines = [line.strip() for line in f_obj.readlines()]
        subs = '+'.join(lines)
    return subs


def main():
    # Setup Envroment
    watched_s = load_subrredits(Path(__file__).parent / 'subreddits.txt')
    reddit = praw.Reddit('f1_predictor_bot')

    # Get the subreedit object
    subs = reddit.subreddit(watched_s)

    # Actual bot logic
    inspect_comments(subs)


if __name__ == "__main__":
    main()
