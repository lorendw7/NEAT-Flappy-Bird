from tkinter import font

import pygame
import random
import os
import time
import neat

# 初始化 Pygame 的字体模块
pygame.font.init()

# 游戏窗口宽度（像素）
WIN_WIDTH = 500
# 游戏窗口高度（像素）
WIN_HEIGHT = 800

# 加载管道图片，并将其放大到原来的2倍（scale2x）
# os.path.join 用于安全拼接路径，避免不同系统路径分隔符的问题
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'pipe.png')))
# 加载地面图片，并放大2倍
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'base.png')))
# 加载背景图片，并放大2倍
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bg.png')))
# 加载小鸟的3张动画帧图片，分别放大2倍，并存入列表，用于扇翅膀动画
BIRD_IMGS = [
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird1.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird2.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird3.png')))
]

# 创建字体对象，用于显示游戏分数等文本
# 使用 "Comic Sans MS" 字体，字号为50
STAT_FONT = pygame.font.SysFont('comicsans', 50)

class Bird:
    IMGS = BIRD_IMGS        # 小鸟的动画帧列表
    MAX_ROTATION = 25        # 小鸟最大倾斜角度（抬头/低头）
    ROT_VEL = 20             # 每帧旋转的速度
    ANIMATION_TIME = 5       # 每帧动画持续的游戏帧数

    def __init__(self, x, y):
        self.x = x  # 小鸟的初始 x 坐标
        self.y = y  # 小鸟的初始 y 坐标
        self.tilt = 0  # 初始倾斜角度为0（水平）
        self.tick_count = 0  # 记录跳跃后经过的帧数，用于计算下落
        self.vel = 0  # 初始速度为0
        self.height = self.y  # 记录跳跃时的起始高度
        self.img_count = 0  # 动画帧计数器
        self.img = self.IMGS[0]  # 当前显示的图片，初始为第一帧

    def jump(self):
        self.vel = -10.5  # 给小鸟一个向上的初速度（y轴向下为正，所以是负数）
        self.tick_count = 0  # 重置计时器，开始新的跳跃周期
        self.height = self.y  # 记录跳跃前的高度，作为抛物线顶点

    def move(self):
        self.tick_count += 1  # 每帧增加计时器

        # 计算位移：s = v₀t + 0.5*at²
        displacement = self.vel * self.tick_count + 0.5 * 3 * self.tick_count ** 2

        # 限制下落速度，避免无限加速
        if displacement >= 16:
            displacement = 16

        # 微调向上跳跃的距离
        if displacement < 0:
            displacement -= 2

        # 更新y坐标
        self.y += displacement

        # 根据运动状态计算倾斜角度
        if displacement < 0 or self.y < self.height + 50:
            # 上升阶段或刚跳起来不久：抬头
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            # 下落阶段：低头
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, screen):
        # 1. 动画帧切换逻辑：控制小鸟扇翅膀的节奏
        self.img_count += 1  # 每过一个游戏帧，动画计数器+1

        # 根据ANIMATION_TIME切换不同的动画帧
        if self.img_count < self.ANIMATION_TIME:
            # 前5帧：显示第0帧- 翅膀上抬
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            # 6-10帧：显示第1帧- 翅膀水平
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            # 11-15帧：显示第2帧- 翅膀下压
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            # 16-20帧：回到第1帧- 翅膀水平
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            # 第21帧：重置计数器，回到第0帧，循环动画
            self.img = self.IMGS[0]
            self.img_count = 0

        # 2. 特殊处理：小鸟垂直下落（倾斜≤-80°）时，停止扇翅膀
        if self.tilt <= -80:
            self.img = self.IMGS[1]  # 强制显示翅膀水平帧
            self.img_count = self.ANIMATION_TIME * 2  # 重置动画计数器，避免切换
            # 解释：设为ANIMATION_TIME*2（10），下次计数会从11开始，直接到第2帧，
            # 但因为tilt≤-80°会一直强制显示第1帧，所以动画暂停

        # 3. 旋转小鸟图片并计算正确的绘制位置
        # 旋转图片：根据当前倾斜角度tilt旋转图片
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        # 计算旋转后的新矩形：保证旋转后图片以原中心为中心，避免位置偏移
        # 步骤：
        # - 先获取原图片的矩形（左上角在(self.x, self.y)）
        original_rect = self.img.get_rect(topleft=(self.x, self.y))
        # - 以原矩形的中心为旋转中心，创建新矩形
        new_rect = rotated_image.get_rect(center=original_rect.center)
        # 4. 绘制旋转后的小鸟到屏幕
        screen.blit(rotated_image, new_rect.topleft)
    def get_mask(self):
        # 从当前小鸟图片（self.img）生成一个掩模对象
        # 掩模会记录图片中每个像素是否为透明（alpha=0），
        # 用于判断小鸟与管道等物体是否发生像素级碰撞，而非简单的矩形碰撞
        return pygame.mask.from_surface(self.img)


class Pipe:
    """
    表示游戏中的管道对象（一对上下管道，中间有间隙供小鸟通过）
    """
    # 上下管道之间的间隙大小（固定值 200 像素）
    GAP = 200
    # 管道向左移动的速度（固定值 5 像素/帧）
    VEL = 5

    def __init__(self, x):
        """
        初始化管道对象
        :param x: 管道的初始 x 坐标（管道是从右向左移动的）
        """
        # 管道的 x 坐标（水平位置）
        self.x = x
        # 管道高度（由 set_height 方法随机生成）
        self.height = 0

        # 上管道的 y 坐标（顶部位置）
        self.top = 0
        # 下管道的 y 坐标（底部位置）
        self.bottom = 0

        # 上管道图片：将原始管道图片垂直翻转，作为顶部管道
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        # 下管道图片：直接使用原始管道图片
        self.PIPE_BOTTOM = PIPE_IMG

        # 标记小鸟是否已经通过这对管道（用于计分）
        self.passed = False

        # 调用 set_height 方法，随机生成管道高度和位置
        self.set_height()

    def set_height(self):
        """
        随机设置管道的高度，从而确定上下管道的位置
        从屏幕顶部开始计算高度
        """
        # 随机生成一个 50 到 450 之间的高度值，作为间隙的中心高度
        self.height = random.randrange(50, 450)
        # 计算上管道的 y 坐标：让上管道的底部刚好落在 self.height 位置
        self.top = self.height - self.PIPE_TOP.get_height()
        # 计算下管道的 y 坐标：让下管道的顶部刚好在 self.height + GAP 位置
        self.bottom = self.height + self.GAP

    def move(self):
        # 管道向左移动：每帧减少x坐标，模拟小鸟向前飞的视觉效果
        self.x -= self.VEL

    def draw(self, win):
        # 绘制上管道：将上管道图片绘制到窗口的 (self.x, self.top) 位置
        win.blit(self.PIPE_TOP, (self.x, self.top))
        # 绘制下管道：将下管道图片绘制到窗口的 (self.x, self.bottom) 位置
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        # 获取小鸟的碰撞掩模（用于精确碰撞检测）
        bird_mask = bird.get_mask()
        # 生成上管道的碰撞掩模
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        # 生成下管道的碰撞掩模
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # 计算上管道相对于小鸟的偏移量（用于掩模碰撞检测）
        # offset = (管道x - 小鸟x, 管道y - 小鸟y)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        # 计算下管道相对于小鸟的偏移量
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # 检测小鸟掩模与上管道掩模是否重叠
        # 如果重叠，返回重叠点坐标；否则返回 None
        t_point = bird_mask.overlap(top_mask, top_offset)
        # 检测小鸟掩模与下管道掩模是否重叠
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)

        # 如果与上管道或下管道任意一个发生重叠，就判定为碰撞
        if t_point or b_point:
            return True

        # 没有碰撞
        return False

class Base:
    # 地面向左移动的速度（与管道速度保持一致，营造小鸟向前飞的效果）
    VEL = 5
    # 地面图片的宽度（从BASE_IMG中获取）
    WIDTH = BASE_IMG.get_width()
    # 地面图片素材（全局加载的BASE_IMG）
    IMG = BASE_IMG

    def __init__(self, y):
        # 地面的y坐标（固定在屏幕底部）
        self.y = y
        # 第一张地面图片的x坐标（初始在屏幕最左侧）
        self.x1 = 0
        # 第二张地面图片的x坐标（初始在第一张图片的右侧，无缝拼接）
        self.x2 = self.WIDTH

    def move(self):
        """
        让地面向左滚动，实现无限循环的地面效果
        """
        # 两张地面图片同时向左移动
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # 当第一张图片完全移出屏幕左侧时，将它移到第二张图片的右侧，继续循环
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        # 当第二张图片完全移出屏幕左侧时，将它移到第一张图片的右侧，继续循环
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    # 绘制地面到游戏窗口
    def draw(self, win):
        # 在 (self.x1, self.y) 位置绘制第一张地面图片
        win.blit(self.IMG, (self.x1, self.y))
        # 在 (self.x2, self.y) 位置绘制第二张地面图片
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, bird, pipes, base, score):
    # 绘制背景图：将背景图片 BG_IMG 绘制到窗口的左上角 (0, 0)
    win.blit(BG_IMG, (0, 0))
    # 遍历所有管道对象，依次绘制到窗口上
    for pipe in pipes:
        pipe.draw(win)

    # 渲染分数文本：
    # "Score: " + str(score)：要显示的文本内容
    # True：开启抗锯齿，让文字更平滑
    # (255, 255, 255)：文字颜色为白色
    text = STAT_FONT.render("Score: " + str(score), True, (255, 255, 255))
    # 将分数文本绘制到窗口右上角
    # x坐标：窗口宽度 - 10（右边距）- 文本宽度，实现右对齐
    # y坐标：距离顶部10像素
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    # 调用小鸟对象的 draw 方法，将小鸟绘制到窗口上
    bird.draw(win)
    # 更新整个屏幕的显示，把这一帧的所有绘制内容呈现出来
    pygame.display.update()


def main():
    # ========== 游戏初始化 ==========
    # 创建小鸟对象，初始位置设置在 (230, 350)（屏幕偏中下位置，更符合游戏初始体验）
    bird = Bird(230, 350)
    # 初始化管道列表，先创建一根管道，初始x坐标600（屏幕右侧外，准备进入画面）
    pipes = [Pipe(600)]
    # 创建地面对象，y坐标730（接近屏幕底部，符合Flappy Bird地面位置）
    base = Base(730)
    # 创建游戏窗口，尺寸为预定义的宽高常量
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    # 创建时钟对象，用于控制游戏帧率，保证不同设备运行速度一致
    clock = pygame.time.Clock()

    # 初始化游戏分数为0
    score = 0

    # 游戏主循环的运行标志（True表示游戏运行，False则退出）
    run = True
    # ========== 游戏主循环 ==========
    while run:
        # 限制游戏帧率为30 FPS，即每秒最多执行30次循环，避免游戏速度过快
        clock.tick(30)

        # ========== 事件处理 ==========
        # 遍历所有Pygame事件（用户输入/系统事件）
        for event in pygame.event.get():
            # 检测到关闭窗口事件时，终止主循环
            if event.type == pygame.QUIT:
                run = False

        # ========== 小鸟运动（当前被注释，如需启用需取消注释） ==========
        # bird.move()  # 更新小鸟的位置、角度、动画帧等物理状态

        # ========== 管道逻辑处理 ==========
        rem = []  # 存储需要删除的管道（已移出屏幕的管道）
        add_pipe = False  # 标记是否需要新增管道（小鸟飞过当前管道后）

        # 遍历所有管道，处理每个管道的移动、碰撞、删除逻辑
        for pipe in pipes:
            # 让管道向左移动（模拟小鸟向前飞）
            pipe.move()

            # 检测小鸟是否与当前管道碰撞（碰撞后暂时pass，可后续添加游戏结束逻辑）
            if pipe.collide(bird):
                pass

            # 如果管道完全移出屏幕左侧（x坐标 + 管道宽度 < 0），加入待删除列表
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            # 如果小鸟飞过当前管道（管道未标记为passed，且管道x坐标 < 小鸟x坐标）
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True  # 标记该管道已被飞过
                add_pipe = True  # 标记需要新增一根管道

        # 如果小鸟飞过管道，分数+1，并在屏幕右侧新增一根管道
        if add_pipe:
            score += 1
            pipes.append(Pipe(600))

        # 移除所有已移出屏幕的管道，释放内存
        for r in rem:
            pipes.remove(r)

        # ========== 地面碰撞检测 ==========
        # 如果小鸟的底部超过地面y坐标（730），说明撞到地面（暂时pass，可添加游戏结束逻辑）
        if bird.y + bird.img.get_height() > 730:
            pass

        # ========== 地面移动 ==========
        base.move()  # 让地面向左滚动，实现无限地面效果

        # ========== 画面绘制 ==========
        # 绘制当前帧的所有元素：背景、管道、分数、地面、小鸟，并更新屏幕
        draw_window(win, bird, pipes, base, score)  # 注：原代码漏传score参数，此处补全，否则分数无法显示

    # ========== 游戏退出 ==========
    pygame.quit()  # 退出Pygame模块
    quit()  # 终止Python程序

# 调用 main 函数，启动游戏
main()