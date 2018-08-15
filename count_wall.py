# Description:
# Fill field "TOKEN" with your token and "GROUP_ID" with target group id.

# Requirements:
# requests

# Author:
# @michaelkrukov / michaelkrukov.ru

import datetime, requests, json, time, math
from copy import deepcopy


# Fill here
TOKEN = ""
GROUP_ID = ""
CHECK_COMMENTS = True
URL = "https://api.vk.com/method/{{key}}?access_token={}&v=5.74".format(TOKEN)

# Some constants
COUNT_STEP = 100
EXECUTE_SIZE = 25

def counter(amount=EXECUTE_SIZE):
    for i in range(amount):
        yield

def req(key, **params):
    r = requests.post(URL.format(key=key), data=params)
    time.sleep(0.35)

    try:
        j = r.json()
    except ValueError:
        print(r.text)
        return None

    if "error" in j:
        print(j)
        return None

    return j["response"]

def executable(key, **params):
    result = "API.{}({{".format(key)

    for k, v in params.items():
        result += '"{}": '.format(k)

        if isinstance(v, str):
            result += '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "<br>") + '"'
        elif isinstance(v, int):
            result += str(v)
        else:
            continue

        result += ","

    return result + "})"

def execute(executables):
    code = "return ["

    for ex in executables:
        code += ex
        code += ","

    code += "];"

    return req("execute", code=code)

def collect_profiles(collection, profiles):
    for p in profiles:
        if p["id"] in collection:
            continue

        collection[p["id"]] = {
            "name": p.get("first_name", "?") + " " +
                p.get("last_name", "?") + " (vk.com/id" + str(p["id"]) + ")",
            "likes_day": 0, "likes_week": 0, "likes_month": 0
        }

def main():
    # Time constants
    current_day = datetime.datetime.now().replace(minute=0, hour=0, second=0, microsecond=0).timestamp()

    day_ago = current_day - 24 * 60 * 60
    week_ago = current_day - 7 * 24 * 60 * 60
    month_ago = current_day - 4 * 7 * 24 * 60 * 60

    print("> script is started...")

    # Get initial data
    wall = req("wall.get", owner_id="-" + str(GROUP_ID), count=COUNT_STEP)
    owner_only_wall = req("wall.get", owner_id="-" + str(GROUP_ID), count=COUNT_STEP, filter="owner")

    count = wall["count"]
    owner_count = owner_only_wall["count"]
    others_count = count - owner_count

    profiles = {}
    result = {
        "amounts": {"day": 0, "week": 0, "month": 0, "all": count},
        "amounts_others_only": {"day": 0, "week": 0, "month": 0, "all": others_count},
        "amounts_owner_only": {"day": 0, "week": 0, "month": 0, "all": owner_count}
    }

    day_comments = []
    week_comments = []
    month_comments = []

    current_offset = 0
    current_requests = []

    posts_ready = False

    while not posts_ready and current_offset < count:
        current_requests.clear()

        for _ in counter(4):
            if current_offset >= count:
                break

            current_requests.append(
                executable(
                    "wall.get",
                    owner_id="-" + str(GROUP_ID),
                    count=COUNT_STEP,
                    offset=current_offset
                )
            )

            current_offset += COUNT_STEP

        post_max_likes_count = -1
        post_max_likes = ""

        post_max_likes_count_week = -1
        post_max_likes_week = ""

        print("> getting and processing posts up to {}...".format(current_offset))

        for res in execute(current_requests):
            for post in res["items"]:
                if post["date"] >= day_ago:
                    result["amounts"]["day"] += 1
                    result["amounts"]["week"] += 1
                    result["amounts"]["month"] += 1

                    if post["from_id"] == post["owner_id"]:
                        result["amounts_owner_only"]["day"] += 1
                        result["amounts_owner_only"]["week"] += 1
                        result["amounts_owner_only"]["month"] += 1
                    else:
                        result["amounts_others_only"]["day"] += 1
                        result["amounts_others_only"]["week"] += 1
                        result["amounts_others_only"]["month"] += 1

                    day_comments.append([post["owner_id"], post["id"], 0, "day"])

                    if post["likes"]["count"] >= post_max_likes_count_week:
                        post_max_likes_count_week = post["likes"]["count"]
                        post_max_likes_week = "vk.com/wall" + str(post["owner_id"]) + \
                            "_" + str(post["id"])

                elif post["date"] >= week_ago:
                    result["amounts"]["week"] += 1
                    result["amounts"]["month"] += 1

                    if post["from_id"] == post["owner_id"]:
                        result["amounts_owner_only"]["week"] += 1
                        result["amounts_owner_only"]["month"] += 1
                    else:
                        result["amounts_others_only"]["week"] += 1
                        result["amounts_others_only"]["month"] += 1

                    week_comments.append([post["owner_id"], post["id"], 0, "week"])

                    if post["likes"]["count"] >= post_max_likes_count_week:
                        post_max_likes_count_week = post["likes"]["count"]
                        post_max_likes_week = "vk.com/wall" + str(post["owner_id"]) + \
                            "_" + str(post["id"])

                elif post["date"] >= month_ago:
                    result["amounts"]["month"] += 1

                    if post["from_id"] == post["owner_id"]:
                        result["amounts_owner_only"]["month"] += 1
                    else:
                        result["amounts_others_only"]["month"] += 1

                    month_comments.append([post["owner_id"], post["id"], 0, "month"])

                else:
                    if not post.get("is_pinned"):
                        posts_ready = True

                    continue

                if post["likes"]["count"] >= post_max_likes_count:
                    post_max_likes_count = post["likes"]["count"]
                    post_max_likes = "vk.com/wall" + str(post["owner_id"]) + \
                        "_" + str(post["id"])

        result["max_likes_post"] = post_max_likes or "Пусто"
        result["max_likes_post_week"] = post_max_likes_week or "Пусто"

    if CHECK_COMMENTS:
        print("> getting and processing comments...")

        new_packs = []
        packs = day_comments + week_comments + month_comments

        while packs:
            current_requests.clear()

            for owner_id, post_id, offset, state in packs:
                current_requests.append(
                    executable("wall.getComments", owner_id=owner_id,
                        post_id=post_id, count=COUNT_STEP, offset=offset,
                        preview_length=1, need_likes=1, extended=1)
                )

            for i in range(math.ceil(len(current_requests) / 25)):
                for pack, res in zip(packs[i*25 : i*25 + 25], execute(current_requests[i*25 : i*25 + 25])):
                    if not res:
                        continue

                    collect_profiles(profiles, res["profiles"])

                    for item in res["items"]:
                        if item["from_id"] not in profiles:
                            continue

                        prof = profiles[item["from_id"]]

                        if pack[3] == "day":
                            prof["likes_day"] += item["likes"]["count"]

                        if pack[3] in ("day", "week"):
                            prof["likes_week"] += item["likes"]["count"]

                        if pack[3] in ("day", "week", "month"):
                            prof["likes_month"] += item["likes"]["count"]

                    if pack[2] + COUNT_STEP < res["count"]:
                        new_packs.append([pack[0], pack[1], pack[2] + COUNT_STEP, pack[3]])

            packs = new_packs
            new_packs = []

    result["profiles"] = profiles

    if CHECK_COMMENTS:
        result["top_commentors_day"] = sorted(profiles.values(), key=lambda x: -x["likes_day"])[:3]
        result["top_commentors_week"] = sorted(profiles.values(), key=lambda x: -x["likes_week"])[:3]
        result["top_commentors_month"] = sorted(profiles.values(), key=lambda x: -x["likes_month"])[:3]

    else:
        result["top_commentors_day"] = []
        result["top_commentors_week"] = []
        result["top_commentors_month"] = []

    return result

if __name__ == "__main__":
    result = main()

    # Little guide by example
    print("\nResult has:", list(result.keys()))

    print("Group id:", GROUP_ID)
    print("Posts:\n", result["amounts"])
    print("Posts from owner:\n", result["amounts_owner_only"])
    print("Posts from others:\n", result["amounts_others_only"])
    print("Most liked posts for last week:\n", result["max_likes_post_week"])
    print("Most liked posts for last month:\n", result["max_likes_post"])
    print("Top commentors for a day:\n", result["top_commentors_day"])
    print("Top commentors for a week:\n", result["top_commentors_week"])
    print("Top commentors for a month:\n", result["top_commentors_month"])
