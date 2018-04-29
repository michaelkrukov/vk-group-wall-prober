# Description / Описание
Простой скрипт для получения базовой информации о стене группы vk. Этот скрипт находит такую информацию:
1. Количество постов открытой стены группы за день\месяц\всего.
2. Топ комментатор (с наибольшим числом лайков) под постами паблика за день\неделю. 
3. Топ пост по лайкам за неделю.
---
A simple script for getting information about a group wall vk. This script finds this information:
1. The number of open group wall posts per day \ month \ total.
2. Top commentator (with the highest number of likes) under public posts for the day / week.
3. Top position in the likes of the week.

# Usage
1. Заполните поле "TOKEN" вашим токеном и "GROUP_ID" id нужной группы.
2. Установите requests (что-то вроде `pip install requests`)
3. Запустите скрипт с помощью python3.6+ (что-то вроде `python count_wall.py`)
---
1. Fill field "TOKEN" with your token and "GROUP_ID" with target group id.
2. Install requests (something like `pip install requests`)
3. Run the script with python3.6+ (something like `python count_wall.py`)

# Example 
```py
if __name__ == "__main__":
    result = main()

    # Little guide by example
    print("\nResult has:", list(result.keys()))

    print("Group id:", GROUP_ID)
    print("Posts:\n", result["amounts"])
    print("Most liked posts:\n", result["max_likes_post"])
    print("Top commentors for a day:\n", result["top_commentors_day"])
    print("Top commentors for a week:\n", result["top_commentors_week"])
```
