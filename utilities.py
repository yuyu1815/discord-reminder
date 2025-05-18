from datetime import datetime
from typing import List, Dict, Optional, Union, Tuple
import discord
from discord.app_commands import Choice

# Format mapping for weekdays
FORMAT_WEEK = {
    "monday": "月",
    "tuesday": "火",
    "wednesday": "水",
    "thursday": "木",
    "friday": "金",
    "saturday": "土",
    "sunday": "日",
}

# Choices for weekdays in Discord UI
WEEK_CHOICES = [
    Choice(name="月", value="monday"),
    Choice(name="火", value="tuesday"),
    Choice(name="水", value="wednesday"),
    Choice(name="木", value="thursday"),
    Choice(name="金", value="friday"),
    Choice(name="土", value="saturday"),
    Choice(name="日", value="sunday"),
]

def create_embed(color: int, title: str, message: str, img_url: Optional[str] = None) -> discord.Embed:
    """
    Create a Discord embed with the given parameters
    
    Args:
        color: Color code in hex format (0xRRGGBB)
        title: Title of the embed
        message: Main content of the embed
        img_url: Optional URL for an image to include
        
    Returns:
        discord.Embed: The created embed
    """
    embed = discord.Embed(title=title, description=message, color=color)
    if img_url and (img_url.startswith("http://") or img_url.startswith("https://")):
        embed.set_image(url=img_url)
    return embed

def create_embed_with_fields(color: int, title: str, fields: List[Dict[str, str]]) -> List[discord.Embed]:
    """
    Create Discord embeds with fields from the provided data
    
    Args:
        color: Color code in hex format (0xRRGGBB)
        title: Title of the embed
        fields: List of dictionaries where each dict contains field name and value pairs
        
    Returns:
        List[discord.Embed]: List of created embeds (multiple if content exceeds Discord limits)
    """
    embeds = [discord.Embed(title=title, color=color)]
    embed_count = 0
    
    for item in fields:
        field_length = 0
        for name, value in item.items():
            # Check if adding this field would exceed Discord's limit
            if len(str(value)) + field_length > 800:
                embed_count += 1
                field_length = 0
                embeds.append(discord.Embed(title=f"{title}({embed_count + 1})", color=color))
            
            embeds[embed_count].add_field(name=name, value=value, inline=True)
            field_length += len(str(value))
    
    return embeds

def format_time(setting_type: str, week: str, day: str, time: str) -> str:
    """
    Format time information based on notification type
    
    Args:
        setting_type: Type of notification (month, week, day, oneday)
        week: Weekday setting
        day: Day setting
        time: Time setting
        
    Returns:
        str: Formatted time string
    """
    time_parts = time.split(':')
    time_str = f"{time_parts[0]}時{time_parts[1]}分{time_parts[2]}秒"
    
    if "month" in setting_type:
        # Monthly notification
        if week and week != "None":
            # Monthly on nth weekday (e.g., 2nd Monday)
            return f"第{day} {FORMAT_WEEK.get(week, week)}曜日 {time_str}"
        else:
            # Monthly on specific day
            return f"{day}日 {time_str}"
    elif "week" in setting_type:
        # Weekly notification
        return f"{FORMAT_WEEK.get(week, week)}曜日 {time_str}"
    elif "day" in setting_type:
        # Daily notification
        return f"{time_str}"
    elif "oneday" in setting_type:
        # One-time notification
        return f"{day.split('/')[0]}月{day.split('/')[1]}日 {time_str}"
    
    return ""

def format_setting(setting: Dict[str, str]) -> Dict[str, str]:
    """
    Format a notification setting for display
    
    Args:
        setting: Dictionary containing notification settings
        
    Returns:
        Dict[str, str]: Formatted setting with id, title, and formatted time
    """
    formatted_time = format_time(
        setting_type=setting["option"],
        week=setting["week"],
        day=setting["day"],
        time=setting["call_time"]
    )
    
    return {
        "id": setting["id"],
        "title": setting["title"],
        "time": formatted_time
    }

def get_day_of_week(date: datetime) -> str:
    """
    Get the day of week as a string
    
    Args:
        date: Datetime object
        
    Returns:
        str: Day of week (monday, tuesday, etc.)
    """
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    return days[date.weekday()]

def should_send_notification(setting: Dict[str, str], current_time: datetime) -> bool:
    """
    Check if a notification should be sent based on the current time
    
    Args:
        setting: The notification setting
        current_time: The current datetime
        
    Returns:
        bool: True if notification should be sent, False otherwise
    """
    option = setting["option"]
    day = setting["day"]
    week = setting["week"]
    call_time = setting["call_time"]
    
    # Convert call_time string to time object
    try:
        time_parts = call_time.split(':')
        notification_time = datetime.strptime(f"{time_parts[0]}:{time_parts[1]}:{time_parts[2]}", "%H:%M:%S").time()
    except (ValueError, IndexError):
        return False
    
    # Check if current time matches notification time (within the same minute)
    current_minute = current_time.strftime("%H:%M")
    notification_minute = f"{notification_time.hour:02d}:{notification_time.minute:02d}"
    
    if current_minute != notification_minute:
        return False
    
    # Check specific conditions based on notification type
    if option == "day":
        # Daily notification - always send if time matches
        return True
    
    elif option == "week":
        # Weekly notification - check day of week
        current_day_of_week = get_day_of_week(current_time)
        return week == current_day_of_week
    
    elif option == "month":
        return _check_monthly_notification(day, week, current_time)
    
    elif option == "oneday":
        return _check_onetime_notification(day, current_time)
    
    return False

def _check_monthly_notification(day: str, week: str, current_time: datetime) -> bool:
    """
    Check if a monthly notification should be sent
    
    Args:
        day: Day setting
        week: Week setting
        current_time: Current datetime
        
    Returns:
        bool: True if notification should be sent, False otherwise
    """
    if week and week != "None":
        # Monthly on nth weekday (e.g., 2nd Monday)
        try:
            target_day = int(day)
            current_day_of_week = get_day_of_week(current_time)
            
            # Check if today is the right weekday
            if current_day_of_week != week:
                return False
            
            # Calculate which occurrence of this weekday in the month
            first_day = current_time.replace(day=1)
            first_weekday_offset = (get_day_of_week(first_day) == week)
            day_in_month = current_time.day
            occurrence = (day_in_month + (6 if first_weekday_offset else 0)) // 7 + first_weekday_offset
            
            return occurrence == target_day
        except (ValueError, TypeError):
            return False
    else:
        # Monthly on specific day
        try:
            target_day = int(day)
            return current_time.day == target_day
        except (ValueError, TypeError):
            return False

def _check_onetime_notification(day: str, current_time: datetime) -> bool:
    """
    Check if a one-time notification should be sent
    
    Args:
        day: Day setting (mm/dd format)
        current_time: Current datetime
        
    Returns:
        bool: True if notification should be sent, False otherwise
    """
    try:
        target_date = datetime.strptime(day, "%m/%d").replace(year=current_time.year)
        # If the date has already passed this year, try next year
        if target_date.date() < current_time.date():
            target_date = target_date.replace(year=current_time.year + 1)
        
        return target_date.date() == current_time.date()
    except (ValueError, TypeError):
        return False