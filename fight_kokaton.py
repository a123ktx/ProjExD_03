import os
import random
import sys
import time
import pygame as pg
import math


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 4 # 爆弾の数を定義
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0) # こうかとんの向きを表すタプル

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        # self.direを更新する
        if sum_mv != [0, 0]:
            self.dire = tuple(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)


# ビームクラス:
class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird:"Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        # bird.direにアクセスする
        self.vx, self.vy = bird.dire
        atan = math.atan2(-self.vy, self.vx)
        self.angle = math.degrees(atan)
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), self.angle, 1)
        self.rct = self.img.get_rect() 
        self.rct.centery = bird.rct.centery + bird.rct.height * (self.vy/5)
        self.rct.left = bird.rct.right + bird.rct.width * (self.vx/5)

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)
        # 壁に当たったビームの判定を画面外に飛ばす
        elif self.rct.center != (-100, -100):
            self.rct.center = (-100, -100)   


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Score:
    """
    スコアを表記するクラス
    """
    def __init__(self, color: tuple[int, int, int]):
        """
        引数に基づきスコアのフォントを作成する
        引数1 : フォントの色
        """
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.num = 0
        self.color = color
        self.img = self.fonto.render(f"スコア：{self.num}", 0, color)
        self.xy = [100, HEIGHT-50]
    
    def update(self, screen:pg.Surface):
        """
        スコアを更新する関数
        引数 screen : 画面Surface
        """
        self.img = self.fonto.render(f"スコア：{self.num}", 0, self.color)
        screen.blit(self.img, self.xy)


class Explosion:
    """
    爆弾にビームを当てた時の爆発を置くクラス
    angleは爆発をflipさせるリスト
    """
    def __init__(self, bomb:Bomb, life: int):
        """
        爆発のイニシャライザ
        引数1 : 爆発する爆弾
        引数2 : 爆発の持続時間
        """
        self.lst = [] # 爆発を入れるリスト
        self.img = pg.image.load(f"fig/explosion.gif") # 元となる爆発
        self.lst.append(self.img)
        self.rct = self.img.get_rect()
        self.lst.append(pg.transform.flip(self.img, True, False))
        self.lst.append(pg.transform.flip(self.img, False, True))
        self.lst.append(pg.transform.flip(self.img, False, False))
        self.lst.append(self.img)
        self.rct.center = bomb.rct.center
        self.life = life
        self.time = 0

    def update(self, screen:pg.Surface):
        """
        爆発を描画する関数
        引数 screen : 画面のSurface
        """
        self.life -= 1
        if self.life > 0:
            if self.time > 5:
                self.time = 0
                self.img = self.lst[self.life%4]
                screen.blit(self.img, self.rct)
            else:
                self.time += 1
                screen.blit(self.img, self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = []
    for i in range(NUM_OF_BOMBS):
        bomb = Bomb((255, 0, 0), 10)
        bombs.append(bomb)
    score = Score((0, 0, 255)) # スコアのイニシャライザを呼び出す
    beams = [] # Beamクラスのインスタンスを複数扱うための空リスト
    explosions = [] # 爆発を入れるリスト
    clock = pg.time.Clock()
    tmr = 0
    beam = None # エラーを回避するために、予め作っておく
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beam = Beam(bird)
                beams.append(beam) # ビームをリストに入れる           
        screen.blit(bg_img, [0, 0])
        
        for b in bombs:
            if b: # 爆弾のNone判定
                if bird.rct.colliderect(b.rct):
                    # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                    # bird.change_img(8, screen)
                    fonto = pg.font.Font(None, 80)
                    txt = fonto.render("Game Over", True, (255, 0, 0))
                    screen.blit(txt, [WIDTH/2-150, HEIGHT/2])
                    pg.display.update()
                    time.sleep(5)
                    return
        
        for i in range(len(bombs)):
            for j in range(len(beams)):
                if beams[j] and bombs[i]:
                    if beams[j].rct.colliderect(bombs[i].rct):
                        # 爆発を発生させる
                        exp = Explosion(bombs[i], 50)
                        explosions.append(exp)
                        # ビームと爆弾が接触した時に、どちらも消滅させる
                        beams[j] = None
                        bombs[i] = None
                        # こうかとんが喜ぶ画像と切り替える
                        bird.change_img(9, screen)
                        #スコアを1増加させる
                        score.num += 1
        
        # 爆弾リスト内にあるNoneを削除する
        while None in bombs:
            bombs.remove(None)
        # ビームリスト内にあるNoneを削除する
        while None in beams:
            beams.remove(None)
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        if beams:
            for beam in beams:
                beam.update(screen)   
        for bomb in bombs:         
            bomb.update(screen)
        for exp in explosions:
            exp.update(screen)
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()