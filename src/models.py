class User:
    def __init__(self, nickname, password, skin_selected=1, level_unlocked=1, score=0, user_id=None):
        self.id = user_id
        self.nickname = nickname
        self.password = password
        self.skin_selected = skin_selected
        self.level_unlocked = level_unlocked
        self.score = score