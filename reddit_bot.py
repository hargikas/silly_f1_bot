import re

import praw
from praw.models import MoreComments

import next_race


def inspect_comments(subreddit):
    total = 0
    replied = 0
    bot_username = 'f1_predictor'
    regex = re.compile(bot_username, re.I)
    try:
        for comment in subreddit.stream.comments(skip_existing=True):
            if isinstance(comment, MoreComments):
                continue
            total += 1

            match = regex.search(comment.body)
            if match:
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

                msg += '*I am a bot, and this action was performed automatically.*'
        
                comment.reply(msg)

    except BaseException:
        print("Parsed %d comments and %d of them where replied" %
              (total, replied))
        raise


def main():
    reddit = praw.Reddit('f1_predictor_bot')
    subreddit = reddit.subreddit("formula1")
    inspect_comments(subreddit)


if __name__ == "__main__":
    main()
