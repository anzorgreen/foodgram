import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const About = ({ updateOrders, orders }) => {
  
  return <Main>
    <MetaTags>
      <title>О проекте</title>
      <meta name="description" content="Фудграм - О проекте" />
      <meta property="og:title" content="О проекте" />
    </MetaTags>
    
    <Container>
      <h1 className={styles.title}>Добро пожаловать!</h1>
      <div className={styles.content}>
        <div>
          <h2 className={styles.subtitle}>Куда ты попал?</h2>
          <div className={styles.text}>
            <p className={styles.textItem}>
                Меня зовут Анзор Квачантирадзе, и я рад приветствовать тебя на своем учебном проекте Foodgram. созданном во время обучения в Яндекс Практикуме. Этот проект — часть учебного курса, но он создан полностью самостоятельно.
            </p>
            <p className={styles.textItem}>
              Цель этого сайта — дать возможность пользователям создавать и хранить рецепты на онлайн-платформе. Кроме того, можно скачать список продуктов, необходимых для
              приготовления блюда, просмотреть рецепты друзей и добавить любимые рецепты в список избранных.
            </p>
            <p className={styles.textItem}>
              Чтобы использовать все возможности сайта — нужна регистрация. Проверка адреса электронной почты не осуществляется, ты можешь ввести любой email. 
            </p>
            <p className={styles.textItem}>
            Я отвечаю за разработку бэкенда этого приложения. В дальнейшем проект не планируется развивать, но если у тебя возникнут вопросы, предложения или комментарии, не стесняйся обращаться. 
            </p>
          </div>
        </div>
        <aside>
          <h2 className={styles.additionalTitle}>
            Ссылки
          </h2>
          <div className={styles.text}>
            <p className={styles.textItem}>
              Код проекта находится <a href="https://github.com/anzorgreen/foodgram.git" className={styles.textLink}>тут</a>
            </p>
            <p className={styles.textItem}>
              Автор проекта: <a href="https://www.instagram.com/anzor_green/" className={styles.textLink}>Анзор Квачантирадзе</a>
              Email: anzor.green@gmail.com
              Telegram: @anzor_green
              Instagram: @anzor_gree
            </p>
          </div>
        </aside>
      </div>
      
    </Container>
  </Main>
}

export default About

