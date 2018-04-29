# Description:
# Fill field "TOKEN" with your token and "GROUP_ID" with target group id.

# Requirements:
# requests

# Author:
# @michaelkrukov / michaelkrukov.ru

import requests, json, time, math
from copy import deepcopy


# Fill here
TOKEN = ""
GROUP_ID = ""
URL = f"https://api.vk.com/method/{{key}}?access_token={TOKEN}&v=5.74"

COUNT_STEP = 100
EXECUTE_SIZE = 25

# user["sex"] = 2(м), 1(ж), 0(?)

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
    result = f"API.{key}({{"

    for k, v in params.items():
        result += f'"{k}": '

        if isinstance(v, str):
            result += '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "<br>") + '"'
        elif isinstance(v, int):
            result += f'{v}'
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
            "likes_day": 0, "likes_week": 0
        }

def main():
    # Some constants
    day_ago = time.time() - 24 * 60 * 60
    week_ago = time.time() - 7 * 24 * 60 * 60

    print("> script is started...")

    # Test for work and receiving "count"
    wall = req("wall.get", owner_id="-" + str(GROUP_ID), count=COUNT_STEP)

    count = wall["count"]

    profiles = {}
    result = {
        "amounts": {"day": 0, "week": 0, "all": count}
    }

    day_comments = []
    week_comments = []

    current_offset = 0
    current_requests = []

    posts_ready = False

    while not posts_ready and current_offset < count:
        current_requests.clear()

        for _ in counter(4):
            if current_offset >= count:
                break

            current_requests.append(
                executable("wall.get", owner_id="-" + str(GROUP_ID), count=COUNT_STEP,
                    offset=current_offset)
            )

            current_offset += COUNT_STEP

        post_max_likes_count = -1
        post_max_likes = ""

        print(f"> getting and processing posts up to {current_offset}...")

        for res in execute(current_requests):
            for post in res["items"]:
                if post["date"] >= day_ago:
                    result["amounts"]["day"] += 1
                    result["amounts"]["week"] += 1
                    day_comments.append([post["owner_id"], post["id"], 0, "day"])
                elif post["date"] >= week_ago:
                    result["amounts"]["week"] += 1
                    week_comments.append([post["owner_id"], post["id"], 0, "week"])
                else:
                    posts_ready = True
                    continue

                if post["likes"]["count"] >= post_max_likes_count:
                    post_max_likes_count = post["likes"]["count"]
                    post_max_likes = "vk.com/wall" + str(post["owner_id"]) + \
                        "_" + str(post["id"])

        result["max_likes_post"] = post_max_likes or "Пусто"

    print(f"> getting and processing comments...")

    new_packs = []
    packs = day_comments + week_comments

    while packs:
        current_requests.clear()

        for owner_id, post_id, offset, state in packs:
            current_requests.append(
                executable("wall.getComments", owner_id=owner_id,
                    post_id=post_id, count=COUNT_STEP, offset=offset,
                    preview_length=1, need_likes=1, extended=1)
            )

        for i in range(math.ceil(len(current_requests)/25)):
            for pack, res in zip(packs[i*25:i*25 + 25], execute(current_requests[i*25:i*25 + 25])):
                collect_profiles(profiles, res["profiles"])

                for item in res["items"]:
                    if item["from_id"] not in profiles:
                        continue

                    prof = profiles[item["from_id"]]

                    if pack[3] == "day":
                        prof["likes_day"] += item["likes"]["count"]

                    if pack[3] in ("day", "week"):
                        prof["likes_week"] += item["likes"]["count"]

                if pack[2] + COUNT_STEP < res["count"]:
                    new_packs.append([pack[0], pack[1], pack[2] + COUNT_STEP, pack[3]])

        packs = new_packs
        new_packs = []

    result["profiles"] = profiles

    result["top_commentors_day"] = sorted(profiles.values(), key=lambda x: -x["likes_day"])[:3]
    result["top_commentors_week"] = sorted(profiles.values(), key=lambda x: -x["likes_week"])[:3]

    return result

if __name__ == "__main__":
    result = main()

    # Little guide by example
    print("\nResult has:", list(result.keys()))

    print("Group id:", GROUP_ID)
    print("Posts:\n", result["amounts"])
    print("Most liked posts:\n", result["max_likes_post"])
    print("Top commentors for a day:\n", result["top_commentors_day"])
    print("Top commentors for a week:\n", result["top_commentors_week"])
