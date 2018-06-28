import sqlalchemy
import db
from db import Task
from Url import Url
from datetime import datetime
from createIssues import make_github_issue


class Message:

    str_help = ""
    u = Url()

    def __init__(self):
        self.str_help = """
                         /new NOME DUEDATE{year-month-day}
                         /todo ID
                         /doing ID
                         /done ID
                         /delete ID
                         /list
                         /rename ID NOME
                         /dependson ID ID...
                         /duplicate ID
                         /priority ID PRIORITY{low, medium, high}
                         /help
                        """

    @staticmethod
    def get_last_update_id(updates):
        update_ids = []
        for update in updates['result']:
            update_ids.append(int(update["update_id"]))
        return max(update_ids)

    def deps_text(self, task, chat, preceed=''):
        text = ''
        for i in range(len(task.dependencies.split(',')[:-1])):
            line = preceed
            dependencies = task.dependencies.split(',')[:-1][i]
            query = db.session.query(Task).filter_by(id=int(dependencies),
                                                     chat=chat)
            dep = query.one()
            icon = '\U0001F195'
            if dep.status == 'DOING':
                icon = '\U000023FA'
            elif dep.status == 'DONE':
                icon = '\U00002611'
            if i + 1 == len(task.dependencies.split(',')[:-1]):
                line += '└── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '    ')
            else:
                line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '│   ')
            text += line
        return text

    def handle_updates(self, updates):
        def new_assigment(msg, chat):
            try:
                date = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]
                duedate = datetime.strptime(date, "%Y-%m-%d").date()
                if duedate >= datetime.today().date():
                    task = Task(chat=chat,
                                name=msg,
                                status='TODO',
                                dependencies='',
                                parents='',
                                priority='',
                                duedate=duedate)
                    db.session.add(task)
                    db.session.commit()
                    make_github_issue(task.name, '')
                    msg_new_task = "New task *TODO* [[{}]] {} ({})"
                    self.u.send_message(msg_new_task.format(task.id,
                                                            task.name,
                                                            task.duedate), chat)
                else:
                    msg_due = "You must inform the task duedate correctly"
                    self.u.send_message(msg_due, chat)
            except IndexError:
                self.u.send_message("You must inform a NAME and DUEDATE", chat)
            except ValueError:
                self.u.send_message("You must inform a DUEDATE correctly", chat)

        def rename_assigment(msg, chat):
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                    msg = msg.split(' ', 1)[0]
            if not msg.isdigit():
                self.u.send_message("You must inform the task id", chat)
            else:
                task_id = int(msg)
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    msg_404 = "_404_ Task {} not found x.x"
                    self.u.send_message(msg_404.format(task_id), chat)
                    return
                if text == '':
                    msg_modify1 = "You want to modify task {}, "
                    msg_modify2 = "but you didn't provide any new text"
                    msg_modify = msg_modify1 + msg_modify2
                    self.u.send_message(msg_modify.format(task_id), chat)
                    return
                old_text = task.name
                task.name = text
                db.session.commit()
                msg_redefined = "Task {} redefined from {} to {}"
                self.u.send_message(msg_redefined.format(task_id,
                                                         old_text,
                                                         text), chat)

        def duplicate_assigment(msg, chat):
            if not msg.isdigit():
                self.u.send_message("You must inform the task id", chat)
            else:
                task_id = int(msg)
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    msg_404 = "_404_ Task {} not found x.x"
                    self.u.send_message(msg_404.format(task_id), chat)
                    return
                dtask = Task(chat=task.chat,
                             name=task.name,
                             status=task.status,
                             dependencies=task.dependencies,
                             parents=task.parents,
                             priority=task.priority,
                             duedate=task.duedate)
                db.session.add(dtask)
                for t in task.dependencies.split(',')[:-1]:
                    qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
                    t = qy.one()
                    t.parents += '{},'.format(dtask.id)
                db.session.commit()
                msg_TODO = "New task *TODO* [[{}]] {}"
                self.u.send_message(msg_TODO.format(dtask.id,
                                                    dtask.name), chat)

        def delete_assigment(msg, chat):
            if not msg.isdigit():
                self.u.send_message("You must inform the task id", chat)
            else:
                task_id = int(msg)
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    msg_404 = "_404_ Task {} not found x.x"
                    self.u.send_message(msg_404.format(task_id), chat)
                    return
                for t in task.dependencies.split(',')[:-1]:
                    qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
                    t = qy.one()
                    t.parents = t.parents.replace('{},'.format(task.id), '')
                db.session.delete(task)
                db.session.commit()
                msg_deleted = "Task [[{}]] deleted"
                self.u.send_message(msg_deleted.format(task_id), chat)

        def todo_assigment(msg, chat):
            id_list = msg.split(" ")
            for id in id_list:
                if not id.isdigit():
                    self.u.send_message("You must inform the task id", chat)
                else:
                    task_id = int(id)
                    query = db.session.query(Task).filter_by(id=task_id,
                                                             chat=chat)
                    try:
                        task = query.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        msg_404 = "_404_ Task {} not found x.x"
                        self.u.send_message(msg_404.format(task_id), chat)
                        return
                    task.status = 'TODO'
                    db.session.commit()
                    msg_TODO = "*TODO* task [[{}]] {}"
                    self.u.send_message(msg_TODO.format(task.id,
                                                        task.name), chat)

        def doing_assigment(msg, chat):
            id_list = msg.split(" ")
            for id in id_list:
                if not id.isdigit():
                    self.u.send_message("You must inform the task id", chat)
                else:
                    task_id = int(id)
                    query = db.session.query(Task).filter_by(id=task_id,
                                                             chat=chat)
                    try:
                        task = query.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        msg_404 = "_404_ Task {} not found x.x"
                        self.u.send_message(msg_404.format(task_id), chat)
                        return
                    task.status = 'DOING'
                    db.session.commit()
                    msg_doing = "*DOING* task [[{}]] {}"
                    self.u.send_message(msg_doing.format(task.id,
                                                         task.name), chat)

        def done_assigment(msg, chat):
            id_list = msg.split(" ")
            for id in id_list:
                if not id.isdigit():
                    self.u.send_message("You must inform the task id", chat)
                else:
                    task_id = int(id)
                    query = db.session.query(Task).filter_by(id=task_id,
                                                             chat=chat)
                    try:
                        task = query.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        msg_404 = "_404_ Task {} not found x.x"
                        self.u.send_message(msg_404.format(task_id), chat)
                        return
                    task.status = 'DONE'
                    db.session.commit()
                    msg_done = "*DONE* task [[{}]] {}"
                    self.u.send_message(msg_done.format(task.id,
                                                        task.name), chat)

        def list_assigment(msg, chat):
            a = ''
            a += '\U0001F4CB Task List\n'
            query = db.session.query(Task).filter_by(parents='',
                                                     chat=chat).order_by(Task.id)
            for task in query.all():
                icon = '\U0001F195'
                if task.status == 'DOING':
                    icon = '\U000023FA'
                elif task.status == 'DONE':
                    icon = '\U00002611'
                a += '[[{}]] {} {} ({})\n'.format(task.id,
                                                  icon,
                                                  task.name,
                                                  task.duedate)
                a += self.deps_text(task, chat)
            self.u.send_message(a, chat)
            a = ''
            a += '\U0001F4DD _Status_\n'
            query = db.session.query(Task).filter_by(status='TODO',
                                                     chat=chat).order_by(Task.id)
            a += '\n\U0001F195 *TODO*\n'

            for task in query.all():
                print(task.name)
                a += '[[{}]] {} ({})\n'.format(task.id,
                                               task.name,
                                               task.duedate)
            query = db.session.query(Task).filter_by(priority='high',
                                                     chat=chat).order_by(Task.id)
            a += '\U0001F6F0 *HIGH*\n'
            for task in query.all():
                a += '[[{}]] {} ({})\n'.format(task.id,
                                               task.name,
                                               task.duedate)
            query = db.session.query(Task).filter_by(priority='medium',
                                                     chat=chat).order_by(Task.id)
            a += '\U0001F6F0 *MEDIUM*\n'
            for task in query.all():
                a += '[[{}]] {} ({})\n'.format(task.id,
                                               task.name,
                                               task.duedate)
            query = db.session.query(Task).filter_by(priority='low',
                                                     chat=chat).order_by(Task.id)
            a += '\U0001F6F0 *LOW*\n'

            for task in query.all():
                a += '[[{}]] {} ({})\n'.format(task.id,
                                               task.name,
                                               task.duedate)
            query = db.session.query(Task).filter_by(status='DOING',
                                                     chat=chat).order_by(Task.id)
            a += '\n\U000023FA *DOING*\n'
            for task in query.all():
                a += '[[{}]] {} ({})\n'.format(task.id,
                                               task.name,
                                               task.duedate)
            query = db.session.query(Task).filter_by(status='DONE',
                                                     chat=chat).order_by(Task.id)
            a += '\n\U00002611 *DONE*\n'
            for task in query.all():
                a += '[[{}]] {} ({})\n'.format(task.id,
                                               task.name,
                                               task.duedate)
            self.u.send_message(a, chat)

        def existing_dependent_task(task, task_dependent):
            query = db.session.query(Task).filter_by(id=task)
            task_dependency = query.one()
            dependencies_task = task_dependency.dependencies.split(",")
            return str(task_dependent) in dependencies_task

        def dependson_assigment(msg, chat):
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]

            if not msg.isdigit():
                return "You must inform the task id"
            else:
                task_id = int(msg)
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    return "_404_ Task {} not found x.x".format(task_id)

                if text == '':
                    for i in task.dependencies.split(',')[:-1]:
                        i = int(i)
                        task_dependency = query.one()
                        task_dependency.parents = task_dependency.parents.replace('{},'.format(task.id), '')

                    task.dependencies = ''
                    msg_dep = "Dependencies removed from task {}"
                    return msg_dep.format(task_id, chat)
                elif existing_dependent_task(text, task_id):
                    msg_dep_t = "Task {} already have a dependency of task {}"
                    return msg_dep_t.format(text, task_id, chat)
                else:
                    for depid in text.split(' '):
                        if not depid.isdigit():
                            msg_all1 = "All dependencies ids must "
                            msg_all2 = "be numeric, and not {}"
                            msg_all = msg_all1 + msg_all2
                            return msg_all.format(depid)
                        else:
                            depid = int(depid)
                            query = db.session.query(Task).filter_by(id=depid,
                                                                     chat=chat)
                            try:
                                task_dependency = query.one()
                                task_dependency.parents += str(task.id) + ','
                            except sqlalchemy.orm.exc.NoResultFound:
                                msg_404 = "_404_ Task {} not found x.x"
                                return msg_404.format(depid)
                                continue

                            deplist = task.dependencies.split(',')
                            if str(depid) not in deplist:
                                task.dependencies += str(depid) + ','
                    if text == '':
                        task.priority = ''
                        msg_prior = "_Cleared_ all priorities from task {}"
                        self.u.send_message(msg_prior.format(task_id), chat)
                    else:
                        if text.lower() not in ['high', 'medium', 'low']:
                            msg_hml1 = "The priority *must be* one of the "
                            msg_hml2 = "following: high, medium, low"
                            msg_hml = msg_hml1 + msg_hml2
                            self.u.send_message(msg_hml, chat)
                        else:
                            task.priority = text.lower()
                            msg_prior = "*Task {}* priority has priority *{}*"
                            self.u.send_message(msg_prior.format(task_id,
                                                                 text.lower()),
                                                chat)
                db.session.commit()
                return "Task {} dependencies up to date".format(task_id)

        def priority_assigment(msg, chat):
                text = ''
                if msg != '':
                    if len(msg.split(' ', 1)) > 1:
                        text = msg.split(' ', 1)[1]
                    msg = msg.split(' ', 1)[0]
                if not msg.isdigit():
                    self.u.send_message("You must inform the task id", chat)
                else:
                    task_id = int(msg)
                    query = db.session.query(Task).filter_by(id=task_id,
                                                             chat=chat)
                    try:
                        task = query.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        msg_404 = "_404_ Task {} not found x.x"
                        self.u.send_message(msg_404.format(task_id), chat)
                        return
                    if text == '':
                        task.priority = ''
                        msg_prior = "_Cleared_ all priorities from task {}"
                        self.u.send_message(msg_prior.format(task_id), chat)
                    else:
                        if text.lower() not in ['high', 'medium', 'low']:
                            msg_hml1 = "The priority *must be* one of the "
                            msg_hml2 = "following: high, medium, low"
                            msg_hml = msg_hml1 + msg_hml2
                            self.u.send_message(msg_hml, chat)
                        else:
                            task.priority = text.lower()
                            msg_prior = "*Task {}* priority has priority *{}*"
                            self.u.send_message(msg_prior.format(task_id,
                                                                 text.lower()), chat)
                    db.session.commit()

        for update in updates["result"]:
            if 'message' in update:
                message = update['message']
            elif 'edited_message' in update:
                message = update['edited_message']
            else:
                print('Can\'t process! {}'.format(update))
                return

            command = message["text"].split(" ", 1)[0]
            msg = ''
            if len(message["text"].split(" ", 1)) > 1:
                msg = message["text"].split(" ", 1)[1].strip()
            chat = message["chat"]["id"]
            print(command, msg, chat)
            if command == '/new':
                new_assigment(msg, chat)
            elif command == '/rename':
                rename_assigment(msg, chat)
            elif command == '/duplicate':
                duplicate_assigment(msg, chat)
            elif command == '/delete':
                delete_assigment(msg, chat)
            elif command == '/todo':
                todo_assigment(msg, chat)
            elif command == '/doing':
                doing_assigment(msg, chat)
            elif command == '/done':
                done_assigment(msg, chat)
            elif command == '/list':
                list_assigment(msg, chat)
            elif command == '/dependson':
                dependson_assigment(msg, chat)
            elif command == '/priority':
                priority_assigment(msg, chat)
            elif command == '/start':
                msg_welcome = "Welcome! Here is a list of things you can do."
                self.u.send_message(msg_welcome, chat)
                self.u.send_message(self.str_help, chat)
            elif command == '/help':
                msg_list = "Here is a list of things you can do."
                self.u.send_message(msg_list, chat)
                self.u.send_message(self.str_help, chat)
            else:
                msg_sorry = "I'm sorry dave. I'm afraid I can't do that."
                self.u.send_message(msg_sorry, chat)
