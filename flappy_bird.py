import pygame
import random
import os
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


def draw_window(win, birds, pipes, base, score):
    """
    绘制游戏每一帧的所有视觉元素
    参数说明：
    - win: pygame游戏窗口对象（画布）
    - birds: 小鸟对象列表（AI控制的所有小鸟）
    - pipes: 管道对象列表（当前屏幕上的所有管道）
    - base: 地面对象（实现滚动效果）
    - score: 当前游戏分数
    """
    # 绘制背景图：将背景图片 BG_IMG 绘制到窗口的左上角 (0, 0)
    win.blit(BG_IMG, (0, 0))

    # 遍历所有管道对象，依次绘制到窗口上（Pipe类的draw方法负责绘制上下两根管道）
    for pipe in pipes:
        pipe.draw(win)

    # 渲染分数文本：
    # STAT_FONT：预加载的字体对象（需提前初始化）
    # "Score: " + str(score)：要显示的文本内容
    # True：开启抗锯齿，让文字边缘更平滑
    # (255, 255, 255)：RGB颜色值，代表白色
    text = STAT_FONT.render("Score: " + str(score), True, (255, 255, 255))

    # 将分数文本绘制到窗口右上角：
    # x坐标：窗口宽度 - 10（右边距）- 文本宽度 → 实现文字右对齐
    # y坐标：10 → 距离顶部10像素的上边距
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    # 遍历所有小鸟对象，绘制到窗口上（Bird类的draw方法负责绘制小鸟图像）
    for bird in birds:
        bird.draw(win)

    # 绘制地面（Base类的draw方法负责绘制滚动的地面）
    base.draw(win)

    # 更新整个屏幕的显示：把当前帧所有绘制的内容一次性呈现出来
    # 注：pygame采用双缓冲机制，需调用此方法才会显示绘制内容
    pygame.display.update()


def main(genomes, config):
    """
    NEAT算法的核心运行函数（每一代种群的游戏循环）
    参数说明：
    - genomes: NEAT库传入的基因组列表（每一个基因组对应一只AI小鸟）
    - config: NEAT配置对象（加载自config_feedforward.txt）
    """

    # --- 1. 在游戏开始前初始化并播放背景音乐 ---
    # 初始化 Pygame 的混音器模块
    pygame.mixer.init()
    # 加载背景音乐文件
    pygame.mixer.music.load('Investigations.mp3')
    # 设置音量（0.0 到 1.0 之间，这里设为50%）
    pygame.mixer.music.set_volume(0.5)
    # 播放音乐，-1 表示无限循环播放
    pygame.mixer.music.play(-1)


    # ========== 初始化种群相关变量 ==========
    birds = []  # 存储所有小鸟对象的列表
    nets = []  # 存储所有神经网络对象的列表（每个小鸟对应一个神经网络）
    ge = []  # 存储所有基因组对象的列表（记录每只小鸟的适应度）

    # 遍历NEAT传入的基因组（genomes是元组列表：(基因组ID, 基因组对象)）
    for _, g in genomes:
        # 根据基因组和配置创建前馈神经网络（小鸟的"大脑"）
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)  # 将神经网络加入列表
        birds.append(Bird(230, 350))  # 创建小鸟对象（初始位置x=230, y=350）
        g.fitness = 0  # 初始化基因组的适应度为0（适应度越高，越容易被保留）
        ge.append(g)  # 将基因组加入列表

    # ========== 游戏元素初始化 ==========
    pipes = [Pipe(600)]  # 初始化管道列表：先创建1根管道，x坐标600（屏幕右侧外，准备进入画面）
    base = Base(730)  # 创建地面对象：y坐标730（接近窗口底部，符合Flappy Bird地面位置）
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))  # 创建游戏窗口（指定宽高）
    clock = pygame.time.Clock()  # 创建时钟对象：用于控制游戏帧率，保证不同设备运行速度一致

    score = 0  # 初始化游戏分数为0（飞过一根管道+1分）
    run = True  # 游戏主循环的运行标志（True=继续运行，False=退出循环）

    # ========== 游戏主循环（每一代种群的生命周期） ==========
    while run:
        # 限制游戏帧率为30 FPS：每秒最多执行30次循环，避免游戏速度过快
        clock.tick(30)

        # ========== 事件处理（用户输入/系统事件） ==========
        for event in pygame.event.get():
            # 检测到"关闭窗口"事件：终止游戏
            if event.type == pygame.QUIT:
                run = False  # 退出主循环
                pygame.quit()  # 关闭pygame模块
                quit()

        # ========== 确定小鸟需要关注的管道（核心逻辑） ==========
        pipe_ind = 0  # 默认关注第0根管道（屏幕中最左侧的管道）
        if len(birds) > 0:  # 如果还有存活的小鸟
            # 如果存在多根管道，且小鸟飞过了第0根管道 → 切换关注第1根管道
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False  # 所有小鸟都死亡 → 终止本轮循环（进入下一代）
            break

        # ========== 每只小鸟的AI决策与适应度更新 ==========
        for x, bird in enumerate(birds):
            bird.move()  # 让小鸟自然下落（Bird类的move方法实现重力效果）
            ge[x].fitness += 0.1  # 每存活一帧，适应度+0.1（鼓励小鸟"活更久"）

            # 神经网络输入（小鸟的3个感知特征）：
            # 1. bird.x：小鸟的x坐标（水平位置）
            # 2. abs(bird.y - pipes[pipe_ind].height)：小鸟与上管道底部的垂直距离
            # 3. abs(bird.y - pipes[pipe_ind].bottom)：小鸟与下管道顶部的垂直距离
            output = nets[x].activate((bird.x,
                                       abs(bird.y - pipes[pipe_ind].height),
                                       abs(bird.y - pipes[pipe_ind].bottom)))

            # 神经网络输出：output[0]是0~1之间的数值（tanh激活函数输出归一化后）
            # 如果输出>0.5 → 让小鸟跳跃（Bird类的jump方法实现向上飞）
            if output[0] > 0.5:
                bird.jump()

        # ========== 管道逻辑处理（移动/碰撞/新增/删除） ==========
        rem = []  # 存储需要删除的管道（已移出屏幕的管道）
        add_pipe = False  # 标记是否需要新增管道（小鸟飞过当前管道后）

        for pipe in pipes:
            pipe.move()  # 让管道向左移动（模拟小鸟向前飞的视觉效果）

            # 检测每只小鸟与管道的碰撞
            for x, bird in enumerate(birds):
                if pipe.collide(bird):  # Pipe类的collide方法检测碰撞
                    ge[x].fitness -= 1  # 碰撞惩罚：适应度-1（鼓励小鸟避开管道）
                    # 移除碰撞的小鸟、对应的神经网络和基因组
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                # 检测小鸟是否飞过管道（未标记passed，且管道x坐标 < 小鸟x坐标）
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True  # 标记该管道已被飞过
                    add_pipe = True  # 标记需要新增一根管道

            # 如果管道完全移出屏幕左侧 → 加入待删除列表（释放内存）
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

        # 小鸟飞过管道：分数+1，所有存活小鸟的适应度+5（奖励正确行为）
        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5  # 飞过管道奖励：适应度+5（比存活奖励更高，引导核心行为）
            pipes.append(Pipe(600))  # 在屏幕右侧新增一根管道

        # 移除所有已移出屏幕的管道
        for r in rem:
            pipes.remove(r)

        # ========== 地面/顶部碰撞检测 ==========
        for x, bird in enumerate(birds):
            # 小鸟撞到地面（y坐标+小鸟高度 > 地面y坐标）或飞出屏幕顶部（y < 0）
            if bird.y + bird.img.get_height() > 730 or bird.y < 0:
                # 移除撞地/出界的小鸟、对应的神经网络和基因组
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        # ========== 地面移动 ==========
        base.move()  # 让地面向左滚动（Base类的move方法实现无限地面效果）

        # ========== 绘制当前帧 ==========
        draw_window(win, birds, pipes, base, score)  # 绘制所有元素并更新屏幕


def run(config_file):
    """
    运行 NEAT 进化算法，训练 Flappy Bird AI
    :param config_file: NEAT 配置文件路径
    """
    # 从配置文件创建 NEAT 配置对象
    # 依次传入：基因组类、繁殖类、物种集合类、停滞检测类、配置文件对象
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_file
    )


    # 创建种群对象，代表当前一代的所有 AI 小鸟
    p = neat.Population(config)

    # 添加标准输出报告器：在控制台打印每一代的进化信息（如适应度、物种数量）
    p.add_reporter(neat.StdOutReporter(True))
    # 添加统计报告器：记录进化过程中的数据（如平均适应度、最优适应度）
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # 运行进化过程：
    # - main：评估函数，用于评估每个基因组（AI小鸟）的适应度
    # - 50：最大进化代数，进化到50代后停止
    winner = p.run(main, 50)

    # 打印最终进化出的最优基因组（表现最好的AI小鸟的“大脑”结构）
    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == '__main__':
    # 获取当前脚本所在目录，用于拼接配置文件路径
    local_dir = os.path.dirname(__file__)
    # 拼接配置文件路径：当前目录下的 config_feedforward.txt
    config_path = os.path.join(local_dir, 'config_feedforward.txt')
    # 调用 run 函数，开始训练 AI
    run(config_path)